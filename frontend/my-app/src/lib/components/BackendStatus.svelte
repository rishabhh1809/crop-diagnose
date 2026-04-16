<script lang="ts">
	import { healthStore } from '$lib/stores/health.svelte';
	import { onMount, onDestroy } from 'svelte';

	onMount(() => healthStore.start());
	onDestroy(() => healthStore.stop());
</script>

{#if !healthStore.isReady}
	<div class="status-bar" class:error={!!healthStore.error}>
		<div class="pulse" aria-hidden="true"></div>
		{#if healthStore.error}
			<span>Cannot reach backend — {healthStore.error}</span>
		{:else if healthStore.loading}
			<span>Connecting to backend…</span>
		{:else}
			<span>Model loading, please wait…</span>
		{/if}
	</div>
{/if}

<style>
	.status-bar {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		z-index: 100;
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 10px 24px;
		background: var(--forest-dark);
		border-bottom: 1px solid var(--forest-canopy);
		font-family: var(--font-mono);
		font-size: 0.78rem;
		color: var(--forest-mist);
		letter-spacing: 0.04em;
	}

	.status-bar.error {
		border-bottom-color: var(--signal-danger);
		color: #f08070;
	}

	.pulse {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: var(--forest-sage);
		animation: pulse 1.4s ease-in-out infinite;
		flex-shrink: 0;
	}

	.status-bar.error .pulse {
		background: var(--signal-danger);
		animation: none;
	}

	@keyframes pulse {
		0%,
		100% {
			opacity: 1;
			transform: scale(1);
		}
		50% {
			opacity: 0.4;
			transform: scale(0.75);
		}
	}
</style>
