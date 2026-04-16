/**
 * lib/stores/prediction.svelte.ts
 * ─────────────────────────
 * Centralised store for the latest prediction result and UI state.
 * Used by both the Upload and LiveStream modes so results render
 * in a shared PredictionPanel without prop-drilling.
 */

import type { PredictResponse } from '$lib/api/client';

// Rolling buffer size for live-stream smoothing.
const BUFFER_SIZE = 3;
// Minimum confidence to show a result (below this → "Scanning…").
export const CONFIDENCE_THRESHOLD = 0.75;

export type PredictionStatus = 'idle' | 'loading' | 'success' | 'error';

class PredictionStore {
	status = $state<PredictionStatus>('idle');
	result = $state<PredictResponse | null>(null);
	error = $state<string | null>(null);
	/** Rolling buffer of recent live predictions for smoothing. */
	buffer = $state<PredictResponse[]>([]);

	setLoading() {
		this.status = 'loading';
		this.error = null;
	}

	setResult(result: PredictResponse) {
		this.status = 'success';
		this.result = result;
		this.error = null;
	}

	/**
	 * Push a live-stream result through the smoothing buffer.
	 * Only updates the displayed result when the top label is stable
	 * across >= ceil(BUFFER_SIZE/2) recent frames, preventing single-frame
	 * false-positive flicker.
	 */
	pushLiveResult(res: PredictResponse) {
		this.buffer = [...this.buffer, res].slice(-BUFFER_SIZE);
		const majority = Math.ceil(BUFFER_SIZE / 2);

		// Count how many of the last N frames agree on the top label.
		const votes = this.buffer.filter((r) => r.label === res.label).length;
		const stable = votes >= majority;

		this.status = 'success';
		if (stable) this.result = res;
		this.error = null;
	}

	setError(err: string) {
		this.status = 'error';
		this.error = err;
	}

	reset() {
		this.status = 'idle';
		this.result = null;
		this.error = null;
		this.buffer = [];
	}

	/** True only when confidence exceeds the display threshold. */
	showResult = $derived(
		this.status === 'success' && this.result && this.result.confidence >= CONFIDENCE_THRESHOLD
	);

	/** Semantic health signal derived from the label string. */
	healthSignal = $derived(
		this.result
			? this.result.label.toLowerCase().includes('healthy')
				? 'healthy'
				: 'diseased'
			: null
	);
}

export const predictionStore = new PredictionStore();
