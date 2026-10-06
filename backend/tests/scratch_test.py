import torch
import numpy as np

def edge_energy(x):
    diff_y = x[:, :, 1:, :] - x[:, :, :-1, :]
    diff_x = x[:, :, :, 1:] - x[:, :, :, :-1]
    return diff_y.abs().mean(dim=[1,2,3]) + diff_x.abs().mean(dim=[1,2,3])

n = 100
s = 256
g = np.random.default_rng(42)

solid = g.random((n, 3, 1, 1), dtype=np.float32).repeat(s, axis=2).repeat(s, axis=3)
gradient = np.zeros((n, 3, s, s), dtype=np.float32)
for i in range(n):
    c1 = g.random((3, 1, 1), dtype=np.float32)
    c2 = g.random((3, 1, 1), dtype=np.float32)
    ramp = np.linspace(0, 1, s, dtype=np.float32).reshape(1, 1, s)
    gradient[i] = c1 * (1 - ramp) + c2 * ramp

x_solid = torch.from_numpy(solid)
x_grad = torch.from_numpy(gradient)

print("Solid edge energy max:", edge_energy(x_solid).max().item())
print("Grad edge energy max:", edge_energy(x_grad).max().item())

# Simulate a real image (random noise is too high, but let's just make a very blurry image)
# We can just see what the threshold should be.
