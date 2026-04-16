/**
 * lib/stores/health.svelte.ts
 * ─────────────────────
 * Polls GET /api/health until the model is loaded, then stops.
 * Components read `healthStore` to gate camera / upload access.
 */

import { getHealth, type HealthResponse } from '$lib/api/client';
import { browser } from '$app/environment';

class HealthStore {
	data = $state<HealthResponse | null>(null);
	loading = $state(true);
	error = $state<string | null>(null);

	isReady = $derived(this.data?.model_loaded === true && this.error === null);

	private pollTimer: ReturnType<typeof setTimeout> | null = null;

	private async poll() {
		try {
			const res = await getHealth();
			this.data = res;
			this.loading = false;
			this.error = null;

			if (!res.model_loaded && browser) {
				// Model still warming up — retry in 2 seconds.
				this.pollTimer = setTimeout(() => this.poll(), 2000);
			}
		} catch (err) {
			this.error = err instanceof Error ? err.message : 'Cannot reach backend.';
			this.loading = false;
			// Retry on error — backend may still be starting.
			if (browser) {
				this.pollTimer = setTimeout(() => this.poll(), 3000);
			}
		}
	}

	start() {
		if (browser) this.poll();
	}

	stop() {
		if (this.pollTimer) clearTimeout(this.pollTimer);
	}
}

export const healthStore = new HealthStore();
