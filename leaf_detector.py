# %% [markdown]
# # Leaf gate: one-class leaf detector (anomaly detection)
#
# Goal: decide "is this a leaf?" **before** the disease classifier runs.
#
# Approach (no non-leaf images needed):
#   1. A frozen, ImageNet-pretrained MobileNetV3-Large turns an image into a
#      960-d embedding.
#   2. We fit a Gaussian to the embeddings of *leaf* images only
#      (PCA -> whitened Mahalanobis distance).
#   3. Distance <= threshold  => leaf     |  distance > threshold => "not a leaf"
#      The threshold is calibrated on the validation split so that
#      REJECT_PERCENTILE % of known-good leaves are accepted.
#
# Everything (normalisation + backbone + PCA + Mahalanobis) is baked into ONE
# ONNX file, so inference needs only onnxruntime. Input convention is identical
# to crop_disease_cnn.onnx: NCHW float32, 256x256, RGB scaled to [0, 1].
#
# Outputs (backend/models/):
#   leaf_detector.onnx   input "input" [N,3,256,256]  ->  output "distance" [N]
#   leaf_detector.json   {"threshold": ..., ...}   (leaf if distance <= threshold)
#
# Training-only deps (not needed by the backend):
#   pip install torch torchvision onnx onnxruntime pillow numpy
# Run as a script (python leaf_detector.py) or cell-by-cell in VS Code (# %%).

# %%
from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import ConcatDataset, DataLoader, Subset
from torchvision import models, transforms
from torchvision.datasets import ImageFolder

# %% [markdown]
# ## Config

# %%
ROOT = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()

DATA_DIR = ROOT / "data"  # expects train/ valid/ (and optionally test/)
OUT_DIR = ROOT / "backend" / "models"
ONNX_PATH = OUT_DIR / "leaf_detector.onnx"
META_PATH = OUT_DIR / "leaf_detector.json"

# Optional: real-world leaf photos (ImageFolder layout: EXTRA_LEAF_DIR/<any>/*.jpg)
# PlantVillage leaves sit on plain backgrounds; adding a few hundred in-the-wild
# leaf photos here makes the gate much less likely to reject real camera frames.
EXTRA_LEAF_DIR: Path | None = None

INPUT_SIZE = 256
TRAIN_PER_CLASS = 100  # images per disease class used to fit the Gaussian
PCA_DIMS = 128
REJECT_PERCENTILE = 99.0  # accept this % of validation leaves (higher = more lenient)
BATCH_SIZE = 64
NUM_WORKERS = 2
SEED = 42
USE_CIFAR_SANITY = False  # downloads CIFAR-10 (~170MB) as a sanity check ONLY

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device:", device)

# %% [markdown]
# ## Data (leaf images only)

# %%
tfm = transforms.Compose(
    [transforms.Resize((INPUT_SIZE, INPUT_SIZE)), transforms.ToTensor()]
)  # -> [0,1], same as the disease model's training/serving pipeline


def sample_per_class(ds: ImageFolder, n: int, rng: random.Random) -> list[int]:
    by_class: dict[int, list[int]] = {}
    for i, t in enumerate(ds.targets):
        by_class.setdefault(t, []).append(i)
    idx: list[int] = []
    for items in by_class.values():
        rng.shuffle(items)
        idx += items[:n]
    return idx


rng = random.Random(SEED)
train_ds = ImageFolder(DATA_DIR / "train", transform=tfm)
fit_sets = [Subset(train_ds, sample_per_class(train_ds, TRAIN_PER_CLASS, rng))]
if EXTRA_LEAF_DIR is not None:
    fit_sets.append(ImageFolder(EXTRA_LEAF_DIR, transform=tfm))
fit_ds = ConcatDataset(fit_sets)
valid_ds = ImageFolder(DATA_DIR / "valid", transform=tfm)
test_dir = DATA_DIR / "test"
test_ds = ImageFolder(test_dir, transform=tfm) if test_dir.exists() else None
print(
    f"fit={len(fit_ds)}  valid={len(valid_ds)}  test={len(test_ds) if test_ds else 0}"
)

# %% [markdown]
# ## Frozen pretrained feature extractor


# %%
class FeatureExtractor(nn.Module):
    """ImageNet normalisation + MobileNetV3-Large backbone -> [N, 960]."""

    def __init__(self) -> None:
        super().__init__()
        weights = models.MobileNet_V3_Large_Weights.IMAGENET1K_V2
        backbone = models.mobilenet_v3_large(weights=weights)
        self.features = backbone.features
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.register_buffer(
            "mean", torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
        )
        self.register_buffer(
            "std", torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = (x - self.mean) / self.std
        return self.pool(self.features(x)).flatten(1)


extractor = FeatureExtractor().to(device).eval()


@torch.no_grad()
def embed(dataset) -> np.ndarray:
    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        num_workers=NUM_WORKERS,
        pin_memory=device.type == "cuda",
    )
    out = []
    for images, _ in loader:
        out.append(extractor(images.to(device)).cpu().numpy())
    return np.concatenate(out).astype(np.float64)


feats_fit = embed(fit_ds)
feats_valid = embed(valid_ds)
feats_test = embed(test_ds) if test_ds else None
print("embedding dim:", feats_fit.shape[1])

# %% [markdown]
# ## Fit the one-class model (PCA + Mahalanobis on leaves only)

# %%
mu = feats_fit.mean(0)
centered = feats_fit - mu
_, S, Vt = np.linalg.svd(centered, full_matrices=False)
comps = Vt[:PCA_DIMS]  # [k, 960]
var = np.maximum(
    S[:PCA_DIMS] ** 2 / (len(centered) - 1), 1e-6
)  # per-component variance


def mahalanobis(feats: np.ndarray) -> np.ndarray:
    z = (feats - mu) @ comps.T
    return (z**2 / var).sum(1)


d_fit, d_valid = mahalanobis(feats_fit), mahalanobis(feats_valid)
threshold = float(np.percentile(d_valid, REJECT_PERCENTILE))


def accept_rate(d: np.ndarray) -> float:
    return float((d <= threshold).mean() * 100)


print(f"threshold (p{REJECT_PERCENTILE}) = {threshold:.2f}")
print(f"leaf accepted  fit  : {accept_rate(d_fit):.2f}%")
print(f"leaf accepted  valid: {accept_rate(d_valid):.2f}%  (calibration set)")
if feats_test is not None:
    print(
        f"leaf accepted  test : {accept_rate(mahalanobis(feats_test)):.2f}%  (honest estimate)"
    )

# %% [markdown]
# ## Bake everything into a single module and export to ONNX


# %%
class LeafGate(nn.Module):
    """[N,3,H,W] in [0,1] -> Mahalanobis distance [N]. Lower = more leaf-like."""

    def __init__(self, extractor: FeatureExtractor, mu, comps, var) -> None:
        super().__init__()
        self.extractor = extractor
        self.register_buffer("mu", torch.tensor(mu, dtype=torch.float32).view(1, -1))
        self.register_buffer(
            "comps", torch.tensor(comps.T, dtype=torch.float32)
        )  # [960,k]
        self.register_buffer(
            "inv_std", torch.tensor(1.0 / np.sqrt(var), dtype=torch.float32).view(1, -1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Reject images with virtually no texture (e.g. solid colours, gradients)
        # by measuring the mean absolute adjacent pixel difference (edge energy).
        diff_y = x[:, :, 1:, :] - x[:, :, :-1, :]
        diff_x = x[:, :, :, 1:] - x[:, :, :, :-1]
        edge_energy = diff_y.abs().mean(dim=[1, 2, 3]) + diff_x.abs().mean(dim=[1, 2, 3])
        
        z = (self.extractor(x) - self.mu) @ self.comps * self.inv_std
        dist = (z * z).sum(dim=1)
        
        # If edge energy is tiny (< 0.015), override distance to be huge (rejected)
        dist = torch.where(edge_energy < 0.015, torch.tensor(1e6, device=x.device, dtype=x.dtype), dist)
        return dist


gate = LeafGate(FeatureExtractor(), mu, comps, var).eval()
gate.extractor.load_state_dict(extractor.state_dict())
gate = gate.to(device).eval()

OUT_DIR.mkdir(parents=True, exist_ok=True)
dummy = torch.randn(1, 3, INPUT_SIZE, INPUT_SIZE, device=device)
export_kwargs = dict(
    export_params=True,
    do_constant_folding=True,
    input_names=["input"],
    output_names=["distance"],
    dynamic_axes={"input": {0: "batch_size"}, "distance": {0: "batch_size"}},
    opset_version=17,
)
try:
    torch.onnx.export(gate, (dummy,), str(ONNX_PATH), dynamo=False, **export_kwargs)
except TypeError:  # older torch without the `dynamo` argument
    torch.onnx.export(gate, (dummy,), str(ONNX_PATH), **export_kwargs)

META_PATH.write_text(
    json.dumps(
        {
            "method": "pretrained mobilenet_v3_large + PCA + mahalanobis (one-class)",
            "decision": "leaf if distance <= threshold",
            "threshold": threshold,
            "reject_percentile": REJECT_PERCENTILE,
            "pca_dims": PCA_DIMS,
            "input_size": INPUT_SIZE,
            "pixel_scale": 1.0 / 255.0,
        },
        indent=2,
    )
)
print("saved:", ONNX_PATH, "and", META_PATH)

# %% [markdown]
# ## Verify the ONNX file matches PyTorch (using onnxruntime, as the backend will)

# %%
import onnxruntime as ort  # noqa: E402

# Prefer CUDA for onnxruntime (needs onnxruntime-gpu); falls back to CPU.
ORT_PROVIDERS = [
    p
    for p in ("CUDAExecutionProvider", "CPUExecutionProvider")
    if p in ort.get_available_providers()
]
sess = ort.InferenceSession(str(ONNX_PATH), providers=ORT_PROVIDERS)
print("onnxruntime providers:", sess.get_providers())
batch = torch.stack(
    [valid_ds[i][0] for i in range(0, len(valid_ds), max(1, len(valid_ds) // 16))][:16]
)
with torch.no_grad():
    ref = gate(batch.to(device)).cpu().numpy()
onnx_out = sess.run(None, {"input": batch.numpy()})[0]
print(
    "max |torch - onnx| =",
    float(np.abs(ref - onnx_out).max()),
    "| distances ~",
    ref[:4],
)

# %% [markdown]
# ## Sanity check: do obvious non-leaves get rejected?
# Synthetic images (and optionally CIFAR-10) are used for **evaluation only** -
# never for training. If rejection is low, lower REJECT_PERCENTILE.


# %%
def distances_onnx(images: np.ndarray) -> np.ndarray:
    return np.concatenate(
        [
            sess.run(None, {"input": images[i : i + BATCH_SIZE]})[0]
            for i in range(0, len(images), BATCH_SIZE)
        ]
    )


def synthetic_negatives(n: int = 128) -> dict[str, np.ndarray]:
    g = np.random.default_rng(SEED)
    s = INPUT_SIZE
    uniform_noise = g.random((n, 3, s, s), dtype=np.float32)
    gauss_noise = np.clip(g.normal(0.5, 0.25, (n, 3, s, s)), 0, 1).astype(np.float32)
    solid = np.broadcast_to(
        g.random((n, 3, 1, 1), dtype=np.float32), (n, 3, s, s)
    ).copy()
    ramp = np.linspace(0, 1, s, dtype=np.float32)
    gradient = np.broadcast_to(
        ramp[None, None, None, :] * g.random((n, 3, 1, 1), dtype=np.float32),
        (n, 3, s, s),
    ).copy()
    return {
        "uniform noise": uniform_noise,
        "gaussian noise": gauss_noise,
        "solid colour": solid,
        "gradient": gradient,
    }


for name, imgs in synthetic_negatives().items():
    rejected = float((distances_onnx(imgs) > threshold).mean() * 100)
    print(f"rejected {name:15s}: {rejected:6.2f}%")

if USE_CIFAR_SANITY:
    from torchvision.datasets import CIFAR10

    cifar = CIFAR10(ROOT / "data_cifar_tmp", train=False, download=True, transform=tfm)
    imgs = torch.stack([cifar[i][0] for i in range(512)]).numpy()
    rejected = float((distances_onnx(imgs) > threshold).mean() * 100)
    print(f"rejected CIFAR-10 objects: {rejected:6.2f}%")

# %% [markdown]
# ## Using it in the backend (later)
# ```python
# dist = session.run(None, {"input": batch})[0]      # same preprocessing as the CNN
# is_leaf = dist <= meta["threshold"]                # else -> "not a leaf"
# ```
