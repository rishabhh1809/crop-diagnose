<script lang="ts">
	import { predictionStore, CONFIDENCE_THRESHOLD } from '$lib/stores/prediction.svelte';
	import { parseLabel, formatConfidence, signalColor } from '$lib/utils/label';

	let result = $derived(predictionStore.result);
	let status = $derived(predictionStore.status);
	let error = $derived(predictionStore.error);
	let parsed = $derived(result ? parseLabel(result.label) : null);
	let color = $derived(
		result && parsed ? signalColor(parsed.isHealthy, result.confidence) : 'var(--forest-sage)'
	);
</script>

<div class="panel" aria-live="polite" aria-label="Prediction result">
	{#if status === 'idle'}
		<div class="state-idle">
			<div class="idle-icon" aria-hidden="true">
				<svg width="32" height="32" viewBox="0 0 32 32" fill="none">
					<circle
						cx="16"
						cy="16"
						r="14"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-dasharray="4 3"
					/>
					<path d="M16 9v7l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
				</svg>
			</div>
			<p>Awaiting analysis</p>
		</div>
	{:else if status === 'loading'}
		<div class="state-loading">
			<div class="spinner" aria-hidden="true"></div>
			<p>Analysing…</p>
		</div>
	{:else if status === 'error'}
		<div class="state-error">
			<p class="error-msg">{error}</p>
		</div>
	{:else if status === 'success' && result && parsed}
		{#if predictionStore.showResult}
			<div class="state-result" style="--signal: {color}">
				<!-- Signal indicator -->
				<div class="signal-dot" aria-hidden="true"></div>

				<!-- Plant name -->
				<p class="plant-name">{parsed.plant}</p>

				<!-- Condition -->
				<h3 class="condition" class:healthy={parsed.isHealthy} class:diseased={!parsed.isHealthy}>
					{parsed.condition}
				</h3>

				<!-- Confidence bar -->
				<div class="confidence-wrap">
					<div class="confidence-bar">
						<div
							class="confidence-fill"
							style="width: {result.confidence * 100}%; background: {color}"
							role="meter"
							aria-valuenow={Math.round(result.confidence * 100)}
							aria-valuemin={0}
							aria-valuemax={100}
							aria-label="Confidence"
						></div>
					</div>
					<span class="confidence-label text-mono">{formatConfidence(result.confidence)}</span>
				</div>

				<!-- Top-k breakdown -->
				{#if result.top_k.length > 1}
					<div class="topk">
						{#each result.top_k.slice(1) as item (item.label)}
							<div class="topk-item">
								<span class="topk-label">{parseLabel(item.label).condition}</span>
								<span class="topk-bar-wrap">
									<span class="topk-bar" style="width: {item.confidence * 100}%"></span>
								</span>
								<span class="topk-pct text-mono">{formatConfidence(item.confidence)}</span>
							</div>
						{/each}
					</div>
				{/if}

				<!-- Latency -->
				<p class="latency text-mono">inference: {result.latency_ms}ms</p>
			</div>
		{:else}
			<!-- Below confidence threshold -->
			<div class="state-scanning warning-state">
				<div class="scan-line" aria-hidden="true"></div>
				<div class="warning-icon" aria-hidden="true">
					<svg width="32" height="32" viewBox="0 0 24 24" fill="none">
						<path
							d="M12 8v4m0 4h.01M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"
							stroke="currentColor"
							stroke-width="1.5"
							stroke-linecap="round"
							stroke-linejoin="round"
						/>
					</svg>
				</div>
				<p>Please show a plant leaf</p>
				<p class="scan-sub text-mono">
					Uncertain observation ({formatConfidence(result?.confidence ?? 0)} / {formatConfidence(
						CONFIDENCE_THRESHOLD
					)})
				</p>
			</div>
		{/if}
	{/if}
</div>

<style>
	.panel {
		background: var(--forest-dark);
		border: 1px solid var(--forest-canopy);
		border-radius: var(--radius-lg);
		padding: var(--space-6);
		min-height: 160px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* ── Idle ── */
	.state-idle {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-3);
		color: var(--forest-fern);
		opacity: 0.6;
		text-align: center;
	}
	.idle-icon {
		color: var(--forest-fern);
	}
	.state-idle p {
		font-size: 0.9rem;
		color: var(--forest-fern);
	}

	/* ── Loading ── */
	.state-loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-3);
	}
	.spinner {
		width: 28px;
		height: 28px;
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
	.state-loading p {
		font-size: 0.9rem;
		color: var(--forest-mist);
	}

	/* ── Error ── */
	.state-error {
		text-align: center;
	}
	.error-msg {
		color: var(--signal-danger);
		font-size: 0.9rem;
	}

	/* ── Result ── */
	.state-result {
		width: 100%;
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
		animation: fadeUp 0.3s var(--ease-out-expo) both;
	}
	@keyframes fadeUp {
		from {
			opacity: 0;
			transform: translateY(8px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.signal-dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--signal);
		box-shadow: 0 0 12px var(--signal);
	}

	.plant-name {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--forest-sage);
		margin: 0;
	}

	.condition {
		font-family: var(--font-display);
		font-size: clamp(1.4rem, 4vw, 2rem);
		font-weight: 700;
		line-height: 1.1;
		color: var(--signal);
	}

	/* ── Confidence bar ── */
	.confidence-wrap {
		display: flex;
		align-items: center;
		gap: var(--space-3);
	}
	.confidence-bar {
		flex: 1;
		height: 4px;
		background: var(--forest-canopy);
		border-radius: var(--radius-full);
		overflow: hidden;
	}
	.confidence-fill {
		height: 100%;
		border-radius: var(--radius-full);
		transition: width 0.4s var(--ease-out-expo);
	}
	.confidence-label {
		font-size: 0.8rem;
		color: var(--forest-mist);
		min-width: 3.5rem;
		text-align: right;
	}

	/* ── Top-k ── */
	.topk {
		display: flex;
		flex-direction: column;
		gap: 6px;
		padding-top: var(--space-2);
		border-top: 1px solid var(--forest-canopy);
	}
	.topk-item {
		display: grid;
		grid-template-columns: 1fr 80px 3rem;
		align-items: center;
		gap: var(--space-2);
		font-size: 0.78rem;
	}
	.topk-label {
		color: var(--forest-mist);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.topk-bar-wrap {
		height: 3px;
		background: var(--forest-canopy);
		border-radius: var(--radius-full);
		overflow: hidden;
	}
	.topk-bar {
		display: block;
		height: 100%;
		background: var(--forest-fern);
		border-radius: var(--radius-full);
	}
	.topk-pct {
		font-size: 0.72rem;
		color: var(--forest-fern);
		text-align: right;
	}

	/* ── Latency ── */
	.latency {
		font-size: 0.7rem;
		color: var(--forest-moss);
		margin: 0;
	}

	/* ── Scanning ── */
	.state-scanning {
		width: 100%;
		text-align: center;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-3);
	}
	.scan-line {
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, transparent, var(--forest-sage), transparent);
		border-radius: var(--radius-full);
		animation: scan 1.8s ease-in-out infinite;
	}
	@keyframes scan {
		0% {
			opacity: 0.3;
			transform: scaleX(0.3);
		}
		50% {
			opacity: 1;
			transform: scaleX(1);
		}
		100% {
			opacity: 0.3;
			transform: scaleX(0.3);
		}
	}
	.state-scanning p {
		color: var(--forest-mist);
		font-size: 0.9rem;
	}
	.scan-sub {
		font-size: 0.72rem;
		color: var(--forest-moss);
	}
	.warning-state p:not(.scan-sub) {
		color: var(--amber-glow);
	}
	.warning-icon {
		color: var(--amber-glow);
		margin-bottom: 4px;
	}
</style>
