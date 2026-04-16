<script lang="ts">
	import { onDestroy } from 'svelte';
	import { predictionStore } from '$lib/stores/prediction.svelte';
	import { openStream, type StreamConnection } from '$lib/api/client';
	import { requestCamera, releaseStream, startCaptureLoop } from '$lib/utils/camera';
	import { healthStore } from '$lib/stores/health.svelte';
	import PredictionPanel from './PredictionPanel.svelte';

	type CameraState = 'idle' | 'requesting' | 'active' | 'error';

	let cameraState: CameraState = $state('idle');
	let cameraError = $state('');
	let facingMode: 'environment' | 'user' = $state('environment');

	let videoEl: HTMLVideoElement;
	let stream: MediaStream | null = null;
	let connection: StreamConnection | null = null;
	let stopCapture: (() => void) | null = null;

	/** True while a frame is in-flight — prevents request pile-up. */
	let inFlight = false;

	async function startCamera() {
		if (!healthStore.isReady) return;
		cameraState = 'requesting';
		cameraError = '';
		predictionStore.reset();

		try {
			stream = await requestCamera(facingMode);
			videoEl.srcObject = stream;
			await videoEl.play();
			cameraState = 'active';
			startStream();
		} catch (err) {
			cameraState = 'error';
			cameraError =
				err instanceof Error
					? err.message
					: 'Camera access denied. Check your browser permissions.';
		}
	}

	function startStream() {
		connection = openStream(
			// onMessage: push result through the smoothing buffer
			(result) => {
				inFlight = false;
				predictionStore.pushLiveResult(result);
			},
			// onError: show non-fatal error but keep streaming
			(error) => {
				inFlight = false;
				predictionStore.setError(error);
			},
			// onOpen: begin frame capture loop
			() => {
				stopCapture = startCaptureLoop(videoEl, sendFrame, 4);
			},
			// onClose
			() => {
				stopCapture?.();
			}
		);
	}

	function sendFrame(blob: Blob) {
		// Skip if previous request still in flight.
		if (inFlight || !connection) return;
		inFlight = true;
		connection.sendFrame(blob);
	}

	function stopCamera() {
		stopCapture?.();
		connection?.close();
		releaseStream(stream);
		stream = null;
		connection = null;
		stopCapture = null;
		inFlight = false;
		cameraState = 'idle';
		predictionStore.reset();
		if (videoEl) {
			videoEl.srcObject = null;
		}
	}

	function flipCamera() {
		facingMode = facingMode === 'environment' ? 'user' : 'environment';
		if (cameraState === 'active') {
			stopCamera();
			startCamera();
		}
	}

	onDestroy(() => stopCamera());
</script>

<div class="live-mode">
	<!-- Video viewport -->
	<div class="video-wrap" class:active={cameraState === 'active'}>
		<video bind:this={videoEl} class="video-feed" playsinline autoplay muted></video>

		{#if cameraState !== 'active'}
			<div class="video-placeholder" aria-hidden="true">
				{#if cameraState === 'requesting'}
					<div class="spinner"></div>
					<p>Requesting camera…</p>
				{:else if cameraState === 'error'}
					<p class="cam-error">{cameraError}</p>
				{:else}
					<!-- Camera icon -->
					<svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
						<path
							d="M6 16a4 4 0 014-4h4l3-4h14l3 4h4a4 4 0 014 4v20a4 4 0 01-4 4H10a4 4 0 01-4-4V16z"
							stroke="currentColor"
							stroke-width="1.5"
						/>
						<circle cx="24" cy="26" r="7" stroke="currentColor" stroke-width="1.5" />
						<circle cx="24" cy="26" r="3" fill="currentColor" opacity="0.4" />
					</svg>
					<p>Camera inactive</p>
				{/if}
			</div>
		{:else}
			<!-- Live indicator -->
			<div class="live-badge" aria-label="Live">
				<span class="live-dot"></span>
				<span class="text-mono">LIVE</span>
			</div>

			<!-- Flip camera button (top-right) -->
			<button class="flip-btn" onclick={flipCamera} title="Flip camera" aria-label="Flip camera">
				<svg width="18" height="18" viewBox="0 0 18 18" fill="none">
					<path
						d="M3 9a6 6 0 006 6 6 6 0 004.24-1.76"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
					/>
					<path
						d="M15 9a6 6 0 00-6-6 6 6 0 00-4.24 1.76"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
					/>
					<path
						d="M13.5 7.5L15 9l1.5-1.5"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
						stroke-linejoin="round"
					/>
					<path
						d="M4.5 10.5L3 9l-1.5 1.5"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
						stroke-linejoin="round"
					/>
				</svg>
			</button>
		{/if}
	</div>

	<!-- Controls -->
	<div class="controls">
		{#if cameraState !== 'active'}
			<button
				class="btn-primary"
				onclick={startCamera}
				disabled={!healthStore.isReady || cameraState === 'requesting'}
				aria-busy={cameraState === 'requesting'}
			>
				{#if cameraState === 'requesting'}
					<span class="btn-spinner"></span> Requesting…
				{:else}
					Start camera
				{/if}
			</button>
		{:else}
			<button class="btn-stop" onclick={stopCamera}> Stop camera </button>
		{/if}

		{#if !healthStore.isReady}
			<span class="disabled-note text-mono">Waiting for model to load…</span>
		{/if}
	</div>

	<!-- Results -->
	<PredictionPanel />
</div>

<style>
	.live-mode {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	/* ── Video wrap ── */
	.video-wrap {
		position: relative;
		width: 100%;
		aspect-ratio: 4 / 3;
		background: var(--forest-dark);
		border: 1px solid var(--forest-canopy);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	@media (max-width: 600px) {
		.video-wrap {
			aspect-ratio: 3 / 4; /* Better fit for portrait phones */
		}
	}

	.video-feed {
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
	}

	/* ── Placeholder ── */
	.video-placeholder {
		position: absolute;
		inset: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: var(--space-3);
		color: var(--forest-fern);
	}
	.video-placeholder p {
		font-size: 0.9rem;
		color: var(--forest-moss);
	}
	.cam-error {
		color: var(--signal-danger) !important;
		text-align: center;
		padding: var(--space-4);
	}

	.spinner {
		width: 32px;
		height: 32px;
		border: 2px solid var(--forest-canopy);
		border-top-color: var(--forest-sage);
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	/* ── Live badge ── */
	.live-badge {
		position: absolute;
		top: 12px;
		left: 12px;
		display: flex;
		align-items: center;
		gap: 6px;
		background: rgba(14, 26, 15, 0.75);
		backdrop-filter: blur(6px);
		border: 1px solid var(--forest-canopy);
		border-radius: var(--radius-full);
		padding: 4px 10px;
		font-size: 0.68rem;
		letter-spacing: 0.12em;
		color: var(--forest-mist);
	}

	.live-dot {
		width: 6px;
		height: 6px;
		background: var(--signal-danger);
		border-radius: 50%;
		animation: livepulse 1.2s ease-in-out infinite;
	}
	@keyframes livepulse {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.3;
		}
	}

	/* ── Flip button ── */
	.flip-btn {
		position: absolute;
		top: 12px;
		right: 12px;
		width: 36px;
		height: 36px;
		border-radius: 50%;
		background: rgba(14, 26, 15, 0.75);
		backdrop-filter: blur(6px);
		border: 1px solid var(--forest-canopy);
		color: var(--forest-mist);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition:
			background var(--duration-fast) ease,
			border-color var(--duration-fast) ease;
	}
	.flip-btn:hover {
		background: var(--forest-mid);
		border-color: var(--forest-fern);
	}

	/* ── Controls ── */
	.controls {
		display: flex;
		align-items: center;
		gap: var(--space-4);
		flex-wrap: wrap;
	}

	.btn-primary {
		display: inline-flex;
		align-items: center;
		gap: var(--space-2);
		background: var(--forest-fern);
		color: var(--forest-void);
		border: none;
		border-radius: var(--radius-md);
		padding: 10px 24px;
		font-family: var(--font-body);
		font-size: 0.9rem;
		font-weight: 500;
		cursor: pointer;
		transition:
			background var(--duration-fast) ease,
			opacity var(--duration-fast) ease;
	}
	.btn-primary:hover:not(:disabled) {
		background: var(--forest-sage);
	}
	.btn-primary:disabled {
		opacity: 0.45;
		cursor: not-allowed;
	}

	.btn-stop {
		display: inline-flex;
		align-items: center;
		gap: var(--space-2);
		background: none;
		color: var(--signal-danger);
		border: 1px solid var(--signal-danger);
		border-radius: var(--radius-md);
		padding: 10px 24px;
		font-family: var(--font-body);
		font-size: 0.9rem;
		font-weight: 500;
		cursor: pointer;
		transition: background var(--duration-fast) ease;
	}
	.btn-stop:hover {
		background: rgba(232, 95, 66, 0.1);
	}

	.btn-spinner {
		width: 14px;
		height: 14px;
		border: 1.5px solid rgba(7, 13, 8, 0.3);
		border-top-color: var(--forest-void);
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
		display: inline-block;
	}

	.disabled-note {
		font-size: 0.75rem;
		color: var(--amber-glow);
	}
</style>
