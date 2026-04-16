/**
 * lib/utils/label.ts
 * ────────────────────
 * Utilities for formatting the raw class label strings that come from the
 * PlantVillage-style dataset (e.g. "Tomato___Late_blight") into human-
 * readable display text.
 */

/**
 * Parse a raw class label into plant and condition parts.
 * Input:  "Tomato___Late_blight"
 * Output: { plant: "Tomato", condition: "Late blight", isHealthy: false }
 */
export function parseLabel(raw: string): {
	plant: string;
	condition: string;
	isHealthy: boolean;
} {
	const [plantRaw, conditionRaw = 'healthy'] = raw.split('___');

	const plant = plantRaw
		.replace(/_/g, ' ')
		.replace(/\(.*?\)/g, '')
		.replace(/,/g, '')
		.trim();

	const condition = conditionRaw.replace(/_/g, ' ').replace(/\s+/g, ' ').trim();

	const isHealthy = condition.toLowerCase() === 'healthy';

	return { plant, condition, isHealthy };
}

/**
 * Format confidence as a percentage string.
 * Input: 0.9421 → "94.2%"
 */
export function formatConfidence(confidence: number): string {
	return `${(confidence * 100).toFixed(1)}%`;
}

/**
 * Return a CSS custom property name for the signal colour based on
 * whether the plant is healthy or diseased and confidence level.
 */
export function signalColor(isHealthy: boolean, confidence: number): string {
	if (confidence < 0.6) return 'var(--forest-sage)';
	if (isHealthy) return 'var(--signal-healthy)';
	if (confidence > 0.85) return 'var(--signal-danger)';
	return 'var(--signal-warning)';
}
