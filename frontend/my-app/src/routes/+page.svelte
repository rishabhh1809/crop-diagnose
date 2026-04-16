<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import ClassesModal from '$lib/components/ClassesModal.svelte';

	let isClassesModalOpen = $state(false);

	function openModal() {
		isClassesModalOpen = true;
	}

	function closeModal() {
		isClassesModalOpen = false;
	}
</script>

<svelte:head>
	<title>CropDiagnose — Plant Health AI</title>
</svelte:head>

<main class="landing">
	<!-- Atmospheric background -->
	<div class="bg-layer" aria-hidden="true">
		<div class="bg-gradient"></div>
		<div class="bg-grid"></div>
		<!-- Floating spore particles -->
		{#each Array(14) as _, i (i)}
			<div
				class="spore"
				style="
				left: {(i * 7.3 + 5) % 100}%;
				animation-delay: -{(i * 1.3).toFixed(1)}s;
				animation-duration: {8 + (i % 5)}s;
				width: {2 + (i % 3)}px;
				height: {2 + (i % 3)}px;
				opacity: {0.15 + (i % 4) * 0.08};
			"
				aria-hidden="true"
			></div>
		{/each}
	</div>

	<!-- Hero -->
	<section class="hero">
		<!-- Decorative leaf mark -->
		<div class="leaf-mark" aria-hidden="true">
			<svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
				<path
					d="M60 10 C60 10, 100 30, 100 70 C100 95, 80 110, 60 110 C40 110, 20 95, 20 70 C20 30, 60 10, 60 10Z"
					stroke="currentColor"
					stroke-width="1"
					fill="none"
				/>
				<path d="M60 10 L60 110" stroke="currentColor" stroke-width="0.75" stroke-dasharray="4 3" />
				<path
					d="M60 40 Q80 50 90 65"
					stroke="currentColor"
					stroke-width="0.75"
					stroke-dasharray="3 3"
				/>
				<path
					d="M60 40 Q40 50 30 65"
					stroke="currentColor"
					stroke-width="0.75"
					stroke-dasharray="3 3"
				/>
				<path
					d="M60 60 Q75 68 82 80"
					stroke="currentColor"
					stroke-width="0.75"
					stroke-dasharray="3 3"
				/>
				<path
					d="M60 60 Q45 68 38 80"
					stroke="currentColor"
					stroke-width="0.75"
					stroke-dasharray="3 3"
				/>
			</svg>
		</div>

		<div class="hero-content">
			<p class="text-mono overline">Plant health intelligence</p>
			<h1 class="hero-title">
				Read what your<br />
				<em>crops are saying</em>
			</h1>
			<p class="hero-body">
				Point your camera at a leaf — or upload an image — and get an instant diagnosis. Powered by
				a custom convolutional neural network trained on 38 disease classes across 14 crop species.
			</p>

			<div class="hero-actions">
				<button class="btn-primary" onclick={() => goto(resolve('/detect'))}>
					Start diagnosing
					<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
						<path
							d="M3 8h10M9 4l4 4-4 4"
							stroke="currentColor"
							stroke-width="1.5"
							stroke-linecap="round"
							stroke-linejoin="round"
						/>
					</svg>
				</button>
				<a href="#how-it-works" class="btn-ghost">How it works</a>
			</div>

			<!-- Stats row -->
			<div class="stats">
				<div
					class="stat clickable"
					role="button"
					tabindex="0"
					onclick={openModal}
					onkeydown={(e) => e.key === 'Enter' && openModal()}
				>
					<span class="stat-value text-mono">38</span>
					<span class="stat-label">disease classes <span class="help-icon">ℹ</span></span>
				</div>
				<div class="stat-divider" aria-hidden="true"></div>
				<div
					class="stat clickable"
					role="button"
					tabindex="0"
					onclick={openModal}
					onkeydown={(e) => e.key === 'Enter' && openModal()}
				>
					<span class="stat-value text-mono">14</span>
					<span class="stat-label">crop species <span class="help-icon">ℹ</span></span>
				</div>
				<div class="stat-divider" aria-hidden="true"></div>
				<div class="stat">
					<span class="stat-value text-mono">&lt;40ms</span>
					<span class="stat-label">inference time</span>
				</div>
			</div>
		</div>
	</section>

	<!-- How it works -->
	<section class="how-it-works" id="how-it-works">
		<p class="section-overline text-mono">Process</p>
		<h2 class="section-title">From leaf to diagnosis</h2>

		<div class="steps">
			<div class="step">
				<div class="step-num text-mono">01</div>
				<h3>Capture</h3>
				<p>
					Use your device camera for real-time streaming, or upload a saved image. The app accepts
					JPEG, PNG, and WebP.
				</p>
			</div>
			<div class="step-connector" aria-hidden="true"></div>
			<div class="step">
				<div class="step-num text-mono">02</div>
				<h3>Preprocess</h3>
				<p>
					Frames are centre-cropped to a square and scaled to 256×256 — identical to how the model
					was trained — preserving leaf shape and colour fidelity.
				</p>
			</div>
			<div class="step-connector" aria-hidden="true"></div>
			<div class="step">
				<div class="step-num text-mono">03</div>
				<h3>Diagnose</h3>
				<p>
					A custom ResNet-style CNN running via ONNX Runtime classifies the leaf. Results include a
					confidence score and the top 3 candidate conditions.
				</p>
			</div>
		</div>
	</section>

	<!-- Modes -->
	<section class="modes">
		<div
			class="mode-card"
			onclick={() => goto(resolve('/detect?mode=upload'))}
			role="button"
			tabindex="0"
			onkeydown={(e) => e.key === 'Enter' && goto(resolve('/detect?mode=upload'))}
		>
			<div class="mode-icon" aria-hidden="true">
				<svg width="28" height="28" viewBox="0 0 28 28" fill="none">
					<rect
						x="1"
						y="1"
						width="26"
						height="26"
						rx="6"
						stroke="currentColor"
						stroke-width="1"
						stroke-dasharray="4 3"
					/>
					<path
						d="M14 18V10M10 14l4-4 4 4"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
						stroke-linejoin="round"
					/>
				</svg>
			</div>
			<h3>Upload image</h3>
			<p>Drag and drop or browse for a leaf photograph. Best for careful single-image analysis.</p>
			<span class="mode-cta text-mono">Open →</span>
		</div>

		<div
			class="mode-card"
			onclick={() => goto(resolve('/detect?mode=live'))}
			role="button"
			tabindex="0"
			onkeydown={(e) => e.key === 'Enter' && goto(resolve('/detect?mode=live'))}
		>
			<div class="mode-icon live" aria-hidden="true">
				<svg width="28" height="28" viewBox="0 0 28 28" fill="none">
					<circle cx="14" cy="14" r="5" fill="currentColor" opacity="0.5" />
					<circle cx="14" cy="14" r="9" stroke="currentColor" stroke-width="1" />
					<circle cx="14" cy="14" r="13" stroke="currentColor" stroke-width="0.5" opacity="0.4" />
				</svg>
			</div>
			<h3>Live detection</h3>
			<p>
				Stream your camera directly. Point at any leaf for instant, continuous prediction at 4 FPS.
			</p>
			<span class="mode-cta text-mono">Open →</span>
		</div>
	</section>

	<!-- Footer -->
	<footer class="footer">
		<p class="text-mono">crop-diagnose · custom CNN · ONNX Runtime · FastAPI · SvelteKit</p>
	</footer>
</main>

<ClassesModal isOpen={isClassesModalOpen} onClose={closeModal} />

<style>
	/* ── Layout ── */
	.landing {
		min-height: 100vh;
		position: relative;
		overflow: hidden;
	}

	/* ── Background ── */
	.bg-layer {
		position: fixed;
		inset: 0;
		z-index: 0;
		pointer-events: none;
	}

	.bg-gradient {
		position: absolute;
		inset: 0;
		background:
			radial-gradient(ellipse 80% 60% at 20% 0%, rgba(45, 74, 48, 0.35) 0%, transparent 60%),
			radial-gradient(ellipse 50% 40% at 85% 90%, rgba(29, 48, 34, 0.4) 0%, transparent 55%),
			var(--forest-void);
	}

	.bg-grid {
		position: absolute;
		inset: 0;
		background-image:
			linear-gradient(rgba(61, 102, 66, 0.06) 1px, transparent 1px),
			linear-gradient(90deg, rgba(61, 102, 66, 0.06) 1px, transparent 1px);
		background-size: 48px 48px;
	}

	/* Floating spore dots */
	.spore {
		position: absolute;
		bottom: -10px;
		background: var(--forest-sage);
		border-radius: 50%;
		animation: float linear infinite;
	}

	@keyframes float {
		0% {
			transform: translateY(0) translateX(0);
			opacity: 0;
		}
		10% {
			opacity: 1;
		}
		90% {
			opacity: 1;
		}
		100% {
			transform: translateY(-100vh) translateX(20px);
			opacity: 0;
		}
	}

	/* ── Sections ── */
	.hero,
	.how-it-works,
	.modes,
	.footer {
		position: relative;
		z-index: 1;
	}

	/* ── Hero ── */
	.hero {
		min-height: 100dvh;
		display: flex;
		align-items: center;
		padding: var(--space-24) var(--space-8) var(--space-16);
		max-width: 1100px;
		margin: 0 auto;
		gap: var(--space-16);
	}

	@media (max-width: 768px) {
		.hero {
			flex-direction: column;
			justify-content: center;
			text-align: center;
			gap: var(--space-8);
			padding-top: var(--space-32);
		}

		.hero-actions {
			justify-content: center;
		}

		.stats {
			justify-content: center;
		}
	}

	.leaf-mark {
		flex-shrink: 0;
		width: clamp(160px, 22vw, 280px);
		color: var(--forest-fern);
		opacity: 0.55;
		animation: sway 8s ease-in-out infinite;
	}

	@keyframes sway {
		0%,
		100% {
			transform: rotate(-2deg);
		}
		50% {
			transform: rotate(2deg);
		}
	}

	.hero-content {
		display: flex;
		flex-direction: column;
		gap: var(--space-6);
	}

	.overline {
		font-size: 0.72rem;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: var(--forest-fern);
		margin: 0;
	}

	.hero-title {
		font-size: clamp(2.8rem, 6vw, 5rem);
		font-weight: 900;
		color: var(--forest-pale);
		line-height: 1.05;
	}

	.hero-title em {
		font-style: italic;
		color: var(--forest-sage);
	}

	.hero-body {
		font-size: 1.05rem;
		line-height: 1.75;
		max-width: 52ch;
		color: var(--forest-mist);
	}

	/* ── CTA buttons ── */
	.hero-actions {
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
		padding: 13px 28px;
		font-family: var(--font-body);
		font-size: 0.95rem;
		font-weight: 500;
		cursor: pointer;
		transition:
			background var(--duration-base) ease,
			transform var(--duration-fast) ease;
	}
	.btn-primary:hover {
		background: var(--forest-sage);
		transform: translateY(-1px);
	}

	.btn-ghost {
		font-size: 0.9rem;
		color: var(--forest-mist);
		border-bottom: 1px solid var(--forest-canopy);
		padding-bottom: 2px;
		transition:
			color var(--duration-fast) ease,
			border-color var(--duration-fast) ease;
	}
	.btn-ghost:hover {
		color: var(--forest-pale);
		border-color: var(--forest-fern);
	}

	/* ── Stats ── */
	.stats {
		display: flex;
		align-items: center;
		gap: var(--space-6);
		flex-wrap: wrap;
	}

	.stat.clickable {
		cursor: pointer;
		padding: var(--space-2) var(--space-3);
		margin: calc(var(--space-2) * -1) calc(var(--space-3) * -1);
		border-radius: var(--radius-sm);
		transition: background var(--duration-fast) ease;
	}
	.stat.clickable:hover,
	.stat.clickable:focus-visible {
		background: rgba(83, 138, 90, 0.1);
	}
	.stat.clickable:hover .help-icon {
		opacity: 1;
	}

	.stat {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.stat-value {
		font-size: 1.4rem;
		font-weight: 500;
		color: var(--forest-pale);
		letter-spacing: -0.02em;
	}

	.stat-label {
		display: flex;
		align-items: center;
		gap: 4px;
		font-size: 0.72rem;
		color: var(--forest-moss);
		letter-spacing: 0.04em;
	}

	.help-icon {
		font-style: normal;
		font-size: 8px;
		width: 12px;
		height: 12px;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		border: 1px solid currentColor;
		border-radius: 50%;
		opacity: 0.4;
		transition: opacity var(--duration-fast) ease;
		transform: translateY(-1px);
	}

	.stat-divider {
		width: 1px;
		height: 32px;
		background: var(--forest-canopy);
	}

	/* ── How it works ── */
	.how-it-works {
		padding: var(--space-24) var(--space-8);
		max-width: 1100px;
		margin: 0 auto;
	}

	.section-overline {
		font-size: 0.7rem;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: var(--forest-fern);
		margin: 0 0 var(--space-3);
	}

	.section-title {
		font-size: clamp(1.8rem, 4vw, 3rem);
		color: var(--forest-pale);
		margin: 0 0 var(--space-12);
	}

	.steps {
		display: flex;
		align-items: flex-start;
		gap: var(--space-4);
		flex-wrap: wrap;
	}

	.step {
		flex: 1;
		min-width: 220px;
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.step-num {
		font-size: 0.7rem;
		letter-spacing: 0.1em;
		color: var(--forest-fern);
	}

	.step h3 {
		font-family: var(--font-display);
		font-size: 1.2rem;
		font-weight: 700;
		color: var(--forest-pale);
	}

	.step p {
		font-size: 0.9rem;
		line-height: 1.7;
		color: var(--forest-mist);
	}

	.step-connector {
		width: 40px;
		height: 1px;
		background: linear-gradient(90deg, var(--forest-fern), transparent);
		margin-top: 50px;
		flex-shrink: 0;
	}

	/* ── Mode cards ── */
	.modes {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: var(--space-4);
		padding: 0 var(--space-8) var(--space-24);
		max-width: 1100px;
		margin: 0 auto;
	}

	.mode-card {
		background: var(--forest-dark);
		border: 1px solid var(--forest-canopy);
		border-radius: var(--radius-xl);
		padding: var(--space-8);
		cursor: pointer;
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
		transition:
			border-color var(--duration-base) ease,
			transform var(--duration-base) var(--ease-out-expo),
			background var(--duration-base) ease;
	}

	.mode-card:hover {
		border-color: var(--forest-fern);
		background: var(--forest-mid);
		transform: translateY(-3px);
	}

	.mode-icon {
		color: var(--forest-fern);
	}
	.mode-icon.live {
		color: var(--signal-danger);
	}

	.mode-card h3 {
		font-family: var(--font-display);
		font-size: 1.3rem;
		font-weight: 700;
		color: var(--forest-pale);
	}

	.mode-card p {
		font-size: 0.88rem;
		line-height: 1.65;
		flex: 1;
	}

	.mode-cta {
		font-size: 0.75rem;
		letter-spacing: 0.06em;
		color: var(--forest-fern);
	}

	/* ── Footer ── */
	.footer {
		border-top: 1px solid var(--forest-dark);
		padding: var(--space-6) var(--space-8);
		text-align: center;
	}

	.footer p {
		font-size: 0.72rem;
		letter-spacing: 0.06em;
		color: var(--forest-moss);
		margin: 0;
	}

	/* ── Responsive ── */
	@media (max-width: 768px) {
		.hero {
			flex-direction: column;
			text-align: center;
			padding: var(--space-16) var(--space-6) var(--space-12);
			min-height: unset;
			gap: var(--space-8);
		}

		.leaf-mark {
			width: 120px;
		}

		.hero-actions,
		.stats {
			justify-content: center;
		}

		.step-connector {
			display: none;
		}

		.steps {
			flex-direction: column;
		}

		.how-it-works,
		.modes {
			padding-left: var(--space-6);
			padding-right: var(--space-6);
		}
	}
</style>
