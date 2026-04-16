<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import UploadMode from '$lib/components/UploadMode.svelte';
	import LiveMode from '$lib/components/LiveMode.svelte';
	import { predictionStore } from '$lib/stores/prediction.svelte';

	// Read ?mode= from URL so deep-linking and landing-page cards work.
	type Mode = 'upload' | 'live';

	let mode = $derived((page.url.searchParams.get('mode') ?? 'upload') as Mode);

	function setMode(m: Mode) {
		predictionStore.reset();
		goto(resolve(`/detect?mode=${m}`), { replaceState: true, noScroll: true });
	}
</script>

<svelte:head>
	<title>Diagnose — CropDiagnose</title>
</svelte:head>

<div class="detect-page">
	<!-- Top bar -->
	<header class="top-bar">
		<a href={resolve('/')} class="back-link" aria-label="Back to home">
			<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
				<path
					d="M13 8H3M7 4l-4 4 4 4"
					stroke="currentColor"
					stroke-width="1.5"
					stroke-linecap="round"
					stroke-linejoin="round"
				/>
			</svg>
			CropDiagnose
		</a>

		<!-- Mode tabs -->
		<div class="tabs" role="tablist" aria-label="Detection mode">
			<button
				role="tab"
				class="tab"
				class:active={mode === 'upload'}
				aria-selected={mode === 'upload'}
				onclick={() => setMode('upload')}
			>
				<svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
					<rect
						x="0.5"
						y="0.5"
						width="13"
						height="13"
						rx="3"
						stroke="currentColor"
						stroke-dasharray="3 2"
					/>
					<path
						d="M7 9V5M5 7l2-2 2 2"
						stroke="currentColor"
						stroke-width="1.2"
						stroke-linecap="round"
						stroke-linejoin="round"
					/>
				</svg>
				Upload
			</button>
			<button
				role="tab"
				class="tab"
				class:active={mode === 'live'}
				aria-selected={mode === 'live'}
				onclick={() => setMode('live')}
			>
				<svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
					<circle cx="7" cy="7" r="2.5" fill="currentColor" opacity="0.6" />
					<circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1" />
				</svg>
				Live
			</button>
		</div>
	</header>

	<!-- Mode panels -->
	<main class="content">
		{#if mode === 'upload'}
			<UploadMode />
		{:else}
			<LiveMode />
		{/if}
	</main>
</div>

<style>
	.detect-page {
		min-height: 100dvh;
		background:
			radial-gradient(ellipse 60% 40% at 50% 0%, rgba(29, 48, 34, 0.6) 0%, transparent 60%),
			var(--forest-void);
		display: flex;
		flex-direction: column;
	}

	/* ── Top bar ── */
	.top-bar {
		position: sticky;
		top: 0;
		z-index: 10;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 14px 24px;
		background: rgba(7, 13, 8, 0.85);
		backdrop-filter: blur(12px);
		border-bottom: 1px solid var(--forest-canopy);
	}

	.back-link {
		display: flex;
		align-items: center;
		gap: 8px;
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--forest-mist);
		letter-spacing: 0.04em;
		transition: color var(--duration-fast) ease;
	}
	.back-link:hover {
		color: var(--forest-pale);
	}

	/* ── Tabs ── */
	.tabs {
		display: flex;
		background: var(--forest-dark);
		border: 1px solid var(--forest-canopy);
		border-radius: var(--radius-md);
		padding: 3px;
		gap: 2px;
	}

	.tab {
		display: flex;
		align-items: center;
		gap: 6px;
		background: none;
		border: none;
		border-radius: 5px;
		padding: 7px 16px;
		font-family: var(--font-body);
		font-size: 0.85rem;
		color: var(--forest-moss);
		cursor: pointer;
		transition:
			background var(--duration-fast) ease,
			color var(--duration-fast) ease;
	}

	.tab:hover {
		color: var(--forest-mist);
	}

	.tab.active {
		background: var(--forest-mid);
		color: var(--forest-pale);
	}

	/* ── Content ── */
	.content {
		flex: 1;
		padding: var(--space-8) var(--space-8);
		max-width: 720px;
		width: 100%;
		margin: 0 auto;
	}

	@media (max-width: 600px) {
		.top-bar {
			padding: 12px 16px;
		}
		.content {
			padding: var(--space-6) var(--space-4);
		}
	}
</style>
