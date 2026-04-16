<script lang="ts">
	import { parseLabel } from '$lib/utils/label';
	import { SvelteMap } from 'svelte/reactivity';

	const rawClasses = [
		'Apple___Apple_scab',
		'Apple___Black_rot',
		'Apple___Cedar_apple_rust',
		'Apple___healthy',
		'Blueberry___healthy',
		'Cherry_(including_sour)___Powdery_mildew',
		'Cherry_(including_sour)___healthy',
		'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot',
		'Corn_(maize)___Common_rust_',
		'Corn_(maize)___Northern_Leaf_Blight',
		'Corn_(maize)___healthy',
		'Grape___Black_rot',
		'Grape___Esca_(Black_Measles)',
		'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)',
		'Grape___healthy',
		'Orange___Haunglongbing_(Citrus_greening)',
		'Peach___Bacterial_spot',
		'Peach___healthy',
		'Pepper,_bell___Bacterial_spot',
		'Pepper,_bell___healthy',
		'Potato___Early_blight',
		'Potato___Late_blight',
		'Potato___healthy',
		'Raspberry___healthy',
		'Soybean___healthy',
		'Squash___Powdery_mildew',
		'Strawberry___Leaf_scorch',
		'Strawberry___healthy',
		'Tomato___Bacterial_spot',
		'Tomato___Early_blight',
		'Tomato___Late_blight',
		'Tomato___Leaf_Mold',
		'Tomato___Septoria_leaf_spot',
		'Tomato___Spider_mites Two-spotted_spider_mite',
		'Tomato___Target_Spot',
		'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
		'Tomato___Tomato_mosaic_virus',
		'Tomato___healthy'
	];

	// Group the raw classes by plant species.
	type CropGroup = {
		plant: string;
		conditions: { name: string; isHealthy: boolean }[];
	};

	let groups: CropGroup[] = [];
	const map = new SvelteMap<string, { name: string; isHealthy: boolean }[]>();

	for (const raw of rawClasses) {
		const { plant, condition, isHealthy } = parseLabel(raw);
		const list = map.get(plant) || [];
		list.push({ name: condition, isHealthy });
		map.set(plant, list);
	}

	for (const [plant, conditions] of map.entries()) {
		// Sort so that "healthy" comes first, then alphabetical.
		conditions.sort((a, b) => {
			if (a.isHealthy) return -1;
			if (b.isHealthy) return 1;
			return a.name.localeCompare(b.name);
		});
		groups.push({ plant, conditions });
	}

	groups.sort((a, b) => a.plant.localeCompare(b.plant));

	let { isOpen = $bindable(false), onClose }: { isOpen: boolean; onClose: () => void } = $props();

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && isOpen) {
			onClose();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if isOpen}
	<div
		class="modal-backdrop"
		onclick={onClose}
		role="presentation"
		aria-hidden="true"
		onkeydown={() => {}}
	>
		<div
			class="modal"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
			role="dialog"
			tabindex="-1"
			aria-modal="true"
			aria-labelledby="modal-title"
		>
			<div class="modal-header">
				<div>
					<h2 id="modal-title" class="title text-mono">Diagnostic Capabilities</h2>
					<p class="subtitle text-mono">14 crop species • 38 disease classes</p>
				</div>
				<button class="close-btn" onclick={onClose} aria-label="Close modal">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
						<path
							d="M18 6L6 18M6 6l12 12"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
						/>
					</svg>
				</button>
			</div>

			<div class="modal-content">
				<div class="grid-list">
					{#each groups as group (group.plant)}
						<div class="crop-group">
							<h3 class="crop-name">{group.plant}</h3>
							<ul class="condition-list">
								{#each group.conditions as cond (cond.name)}
									<li class="condition-item" class:healthy={cond.isHealthy}>
										<div class="dot" aria-hidden="true"></div>
										<span class="condition-name">{cond.name}</span>
									</li>
								{/each}
							</ul>
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		width: 100vw;
		height: 100dvh;
		background: rgba(7, 13, 8, 0.85);
		backdrop-filter: blur(8px);
		z-index: 999;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--space-4);
		animation: fadeIn 0.2s var(--ease-out-expo);
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	.modal {
		background: var(--forest-dark);
		border: 1px solid var(--forest-canopy);
		border-radius: var(--radius-lg);
		width: 100%;
		max-width: 800px;
		max-height: 85dvh;
		display: flex;
		flex-direction: column;
		box-shadow: 0 24px 48px -12px rgba(0, 0, 0, 0.4);
		animation: slideUp 0.3s var(--ease-out-expo);
		overflow: hidden;
	}

	@keyframes slideUp {
		from {
			opacity: 0;
			transform: translateY(20px) scale(0.98);
		}
		to {
			opacity: 1;
			transform: translateY(0) scale(1);
		}
	}

	.modal-header {
		padding: var(--space-6) var(--space-8);
		border-bottom: 1px solid var(--forest-canopy);
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		background: var(--forest-deep);
		flex-shrink: 0;
	}

	.title {
		font-family: var(--font-display);
		font-size: 1.5rem;
		color: var(--forest-pale);
		margin-bottom: var(--space-1);
	}

	.subtitle {
		font-size: 0.85rem;
		color: var(--forest-sage);
		letter-spacing: 0.05em;
		text-transform: uppercase;
	}

	.close-btn {
		background: none;
		border: none;
		color: var(--forest-mist);
		cursor: pointer;
		padding: var(--space-2);
		margin: calc(var(--space-2) * -1);
		border-radius: var(--radius-sm);
		transition:
			color var(--duration-fast) ease,
			background var(--duration-fast) ease;
	}

	.close-btn:hover {
		color: var(--forest-pale);
		background: var(--forest-mid);
	}

	.modal-content {
		padding: var(--space-8);
		overflow-y: auto;
		overscroll-behavior: contain;
	}

	@media (max-width: 600px) {
		.modal-content {
			padding: var(--space-4);
		}
		.modal-header {
			padding: var(--space-4);
		}
		.title {
			font-size: 1.2rem;
		}
		.crop-group {
			gap: var(--space-4);
		}
	}

	.modal-content::-webkit-scrollbar {
		width: 8px;
	}
	.modal-content::-webkit-scrollbar-track {
		background: transparent;
	}
	.modal-content::-webkit-scrollbar-thumb {
		background: var(--forest-canopy);
		border-radius: var(--radius-full);
		border: 2px solid var(--forest-dark);
	}

	.grid-list {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
		gap: var(--space-8) var(--space-6);
	}

	.crop-group {
		display: flex;
		flex-direction: column;
		gap: var(--space-3);
	}

	.crop-name {
		font-family: var(--font-display);
		font-size: 1.15rem;
		color: var(--forest-light);
		border-bottom: 1px dashed var(--forest-moss);
		padding-bottom: 4px;
	}

	.condition-list {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: var(--space-2);
	}

	.condition-item {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 0.85rem;
		color: var(--forest-mist);
		line-height: 1.4;
	}

	.condition-item.healthy {
		color: var(--forest-sage);
	}

	.dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--amber-glow);
		opacity: 0.8;
		flex-shrink: 0;
	}

	.condition-item.healthy .dot {
		background: var(--signal-healthy);
		opacity: 1;
	}

	@media (max-width: 640px) {
		.modal-header {
			padding: var(--space-4) var(--space-6);
		}
		.modal-content {
			padding: var(--space-6);
		}
		.title {
			font-size: 1.25rem;
		}
		.grid-list {
			grid-template-columns: 1fr;
			gap: var(--space-6);
		}
	}
</style>
