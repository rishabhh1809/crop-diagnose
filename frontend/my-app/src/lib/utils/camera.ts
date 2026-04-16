/**
 * lib/utils/camera.ts
 * ─────────────────────
 * Camera access and frame-capture utilities.
 * All camera I/O is isolated here — components stay declarative.
 */

/** Request the device camera. Prefers rear-facing on mobile. */
export async function requestCamera(
	facingMode: 'environment' | 'user' = 'environment'
): Promise<MediaStream> {
	if (!navigator.mediaDevices?.getUserMedia) {
		throw new Error('Camera API is not supported in this browser.');
	}
	return navigator.mediaDevices.getUserMedia({
		video: {
			facingMode,
			width: { ideal: 1280 },
			height: { ideal: 720 }
		},
		audio: false
	});
}

/** Stop all tracks on a media stream. */
export function releaseStream(stream: MediaStream | null): void {
	stream?.getTracks().forEach((t) => t.stop());
}

/**
 * Capture a centre-cropped, resized JPEG Blob from a <video> element.
 *
 * @param video  The playing HTMLVideoElement to sample from.
 * @param size   Output square size in pixels (default 256 — matches model input).
 * @param quality JPEG quality 0–1 (default 0.82).
 * @returns A JPEG Blob ready to send over WebSocket, or null if the video
 *          has no dimensions yet.
 */
export function captureFrame(
	video: HTMLVideoElement,
	size = 256,
	quality = 0.82
): Promise<Blob | null> {
	const { videoWidth: vw, videoHeight: vh } = video;
	if (!vw || !vh) return Promise.resolve(null);

	// Centre-crop to the largest square, then scale to `size`.
	const side = Math.min(vw, vh);
	const sx = (vw - side) / 2;
	const sy = (vh - side) / 2;

	const canvas = document.createElement('canvas');
	canvas.width = size;
	canvas.height = size;
	const ctx = canvas.getContext('2d');
	if (!ctx) return Promise.resolve(null);

	ctx.drawImage(video, sx, sy, side, side, 0, 0, size, size);

	return new Promise((resolve) => {
		canvas.toBlob((blob) => resolve(blob), 'image/jpeg', quality);
	});
}

/**
 * Creates a self-managing frame-capture loop.
 * Pauses automatically when the document is hidden (battery / CPU friendly).
 *
 * @param video      Source video element.
 * @param onFrame    Called with each captured Blob.
 * @param fps        Target frames per second (default 4).
 * @returns A `stop` function that cancels the loop.
 */
export function startCaptureLoop(
	video: HTMLVideoElement,
	onFrame: (blob: Blob) => void,
	fps = 4
): () => void {
	const interval = 1000 / fps;
	let lastCapture = 0;
	let rafId: number;
	let stopped = false;

	async function loop(now: number) {
		if (stopped) return;

		if (!document.hidden && now - lastCapture >= interval) {
			lastCapture = now;
			const blob = await captureFrame(video);
			if (blob && !stopped) onFrame(blob);
		}

		rafId = requestAnimationFrame(loop);
	}

	rafId = requestAnimationFrame(loop);

	return () => {
		stopped = true;
		cancelAnimationFrame(rafId);
	};
}
