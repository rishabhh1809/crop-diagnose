<script lang="ts">
	import { predictionStore } from '$lib/stores/prediction.svelte';
	import { predictImage } from '$lib/api/client';
	import { healthStore } from '$lib/stores/health.svelte';
	import PredictionPanel from './PredictionPanel.svelte';

	let dragOver = $state(false);
	let fileInput: HTMLInputElement;
	let previewUrl: string | null = $state(null);
	let isAnalysing = $state(false);

	async function handleFile(file: File) {
		if (!file.type.startsWith('image/')) {
			predictionStore.setError('Please upload an image file (JPEG, PNG, WebP).');
			return;
		}

		// Show preview immediately.
		if (previewUrl) URL.revokeObjectURL(previewUrl);
		previewUrl = URL.createObjectURL(file);

		predictionStore.reset();
		predictionStore.setLoading();
		isAnalysing = true;

		try {
			const result = await predictImage(file);
			predictionStore.setResult(result);
		} catch (err) {
			predictionStore.setError(err instanceof Error ? err.message : 'Prediction failed.');
		} finally {
			isAnalysing = false;
		}
	}

	function onFileInputChange(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (file) handleFile(file);
		input.value = '';
	}

	function onDrop(e: DragEvent) {
		e.preventDefault();
		dragOver = false;
		const file = e.dataTransfer?.files[0];
		if (file) handleFile(file);
	}

	function onDragOver(e: DragEvent) {
		e.preventDefault();
		dragOver = true;
	}
	function onDragLeave() {
		dragOver = false;
	}

	function clearResult() {
		if (previewUrl) {
			URL.revokeObjectURL(previewUrl);
			previewUrl = null;
		}
		predictionStore.reset();
	}

	import { onDestroy } from 'svelte';
	onDestroy(() => {
		if (previewUrl) URL.revokeObjectURL(previewUrl);
	});
</script>

<div class="upload-mode">
	<!-- Drop Zone -->
	<div
		class="dropzone"
		class:drag-over={dragOver}
		class:has-preview={!!previewUrl}
		role="button"
		tabindex={healthStore.isReady ? 0 : -1}
		aria-disabled={!healthStore.isReady}
		aria-label="Upload leaf image"
		onclick={() => healthStore.isReady && fileInput.click()}
		onkeydown={(e) => e.key === 'Enter' && healthStore.isReady && fileInput.click()}
		ondrop={onDrop}
		ondragover={onDragOver}
		ondragleave={onDragLeave}
	>
		{#if previewUrl}
			<div class="preview-wrap">
				<img src={previewUrl} alt="Uploaded leaf" class="preview-img" />
				{#if isAnalysing}
					<div class="analyse-overlay" aria-label="Analysing">
						<div class="analyse-ring"></div>
					</div>
				{/if}
			</div>
		{:else}
			<div class="dropzone-inner">
				<div class="upload-icon" aria-hidden="true">
					<svg width="40" height="40" viewBox="0 0 40 40" fill="none">
						<rect
							x="1"
							y="1"
							width="38"
							height="38"
							rx="9"
							stroke="currentColor"
							stroke-width="1"
							stroke-dasharray="5 3"
						/>
						<path
							d="M20 26V14M14 20l6-6 6 6"
							stroke="currentColor"
							stroke-width="1.5"
							stroke-linecap="round"
							stroke-linejoin="round"
						/>
					</svg>
				</div>
				<p class="drop-title">Drop a leaf image here</p>
				<p class="drop-sub">or click to browse · JPEG, PNG, WebP</p>
				{#if !healthStore.isReady}
					<span class="drop-disabled text-mono">Waiting for model…</span>
				{/if}
			</div>
		{/if}
	</div>

	<input
		bind:this={fileInput}
		type="file"
		accept="image/jpeg,image/png,image/webp"
		class="sr-only"
		aria-hidden="true"
		onchange={onFileInputChange}
	/>

	<!-- Clear button -->
	{#if previewUrl}
		<button class="clear-btn" onclick={clearResult} aria-label="Clear and upload another">
			Clear
		</button>
	{/if}

	<!-- Results -->
	<PredictionPanel />
</div>

<style>
	.upload-mode {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
	}

	/* ── Drop zone ── */
	.dropzone {
		border: 1px dashed var(--forest-canopy);
		border-radius: var(--radius-lg);
		min-height: 220px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition:
			border-color var(--duration-base) ease,
			background var(--duration-base) ease;
		position: relative;
		overflow: hidden;
		background: var(--forest-dark);
	}

	.dropzone:hover:not([aria-disabled='true']),
	.dropzone:focus-visible {
		border-color: var(--forest-fern);
		background: var(--forest-mid);
	}

	.dropzone.drag-over {
		border-color: var(--forest-sage);
		background: var(--forest-mid);
		border-style: solid;
	}

	.dropzone[aria-disabled='true'] {
		cursor: not-allowed;
		opacity: 0.5;
	}

	/* ── Inner idle state ── */
	.dropzone-inner {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-2);
		padding: var(--space-8);
		text-align: center;
	}

	.upload-icon {
		color: var(--forest-fern);
		margin-bottom: var(--space-2);
	}

	.drop-title {
		font-size: 1rem;
		font-weight: 500;
		color: var(--forest-mist);
		margin: 0;
	}

	.drop-sub {
		font-size: 0.8rem;
		color: var(--forest-moss);
		margin: 0;
	}

	.drop-disabled {
		font-size: 0.72rem;
		color: var(--amber-glow);
		margin-top: var(--space-2);
	}

	/* ── Preview ── */
	.preview-wrap {
		width: 100%;
		height: 100%;
		min-height: 220px;
		position: relative;
	}

	.preview-img {
		width: 100%;
		height: 100%;
		min-height: 220px;
		max-height: 400px;
		object-fit: cover;
		display: block;
	}

	.analyse-overlay {
		position: absolute;
		inset: 0;
		background: rgba(14, 26, 15, 0.55);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.analyse-ring {
		width: 48px;
		height: 48px;
		border: 2px solid rgba(122, 184, 127, 0.25);
		border-top-color: var(--forest-sage);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	/* ── Clear button ── */
	.clear-btn {
		align-self: flex-start;
		background: none;
		border: 1px solid var(--forest-canopy);
		border-radius: var(--radius-md);
		color: var(--forest-mist);
		font-family: var(--font-mono);
		font-size: 0.78rem;
		padding: 6px 16px;
		cursor: pointer;
		transition:
			border-color var(--duration-fast) ease,
			color var(--duration-fast) ease;
	}

	.clear-btn:hover {
		border-color: var(--forest-fern);
		color: var(--forest-pale);
	}
</style>
