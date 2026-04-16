/**
 * lib/api/client.ts
 * ─────────────────
 * Typed API client for the crop-diagnose FastAPI backend.
 *
 * Rules
 * ─────
 * • All fetch/WebSocket calls live here — no raw fetch() elsewhere.
 * • All response shapes are typed — no `any`.
 * • The base URL is read from an environment variable so dev/prod
 *   require zero code changes.
 */

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ClassProbability {
	label: string;
	confidence: number; // [0, 1]
}

export interface PredictResponse {
	label: string;
	confidence: number;
	top_k: ClassProbability[];
	latency_ms: number;
}

export interface HealthResponse {
	status: 'ok' | 'loading';
	model_loaded: boolean;
	num_classes: number;
	input_size: number;
	onnx_providers: string[];
}

export interface ClassesResponse {
	classes: string[];
	num_classes: number;
}

export interface ApiError {
	detail: string;
}

// ── Config ────────────────────────────────────────────────────────────────────

// In dev, Vite proxies /api → http://localhost:8000.
// In prod, set VITE_API_BASE_URL to your deployed API origin.
const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '';

// WebSocket base: ws:// in prod, relative in dev (Vite proxy handles it).
const WS_BASE =
	(import.meta.env.VITE_WS_BASE_URL as string | undefined) ??
	(typeof window !== 'undefined'
		? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
		: '');

// ── HTTP helpers ──────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(`${BASE_URL}${path}`, {
		...init,
		headers: { ...init?.headers }
	});

	if (!res.ok) {
		const err: ApiError = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail ?? `HTTP ${res.status}`);
	}

	return res.json() as Promise<T>;
}

// ── Public API ────────────────────────────────────────────────────────────────

/** Check backend readiness. Poll until model_loaded is true. */
export async function getHealth(): Promise<HealthResponse> {
	return apiFetch<HealthResponse>('/api/health');
}

/** Fetch all disease class labels. */
export async function getClasses(): Promise<ClassesResponse> {
	return apiFetch<ClassesResponse>('/api/classes');
}

/**
 * Upload a single image file for disease prediction.
 * Uses multipart/form-data — matches the UploadFile backend endpoint.
 */
export async function predictImage(file: File): Promise<PredictResponse> {
	const form = new FormData();
	form.append('file', file);
	return apiFetch<PredictResponse>('/api/predict', { method: 'POST', body: form });
}

// ── WebSocket stream ──────────────────────────────────────────────────────────

export type StreamMessageHandler = (result: PredictResponse) => void;
export type StreamErrorHandler = (error: string) => void;

export interface StreamConnection {
	/** Send a raw JPEG Blob to the server for inference. */
	sendFrame(blob: Blob): void;
	/** Cleanly close the connection. */
	close(): void;
}

/**
 * Open a persistent WebSocket connection to /api/stream.
 * Calls onMessage with each PredictResponse, onError on failures.
 * Returns a StreamConnection handle.
 */
export function openStream(
	onMessage: StreamMessageHandler,
	onError: StreamErrorHandler,
	onOpen?: () => void,
	onClose?: () => void
): StreamConnection {
	const url = `${WS_BASE}/api/stream`;
	const ws = new WebSocket(url);
	ws.binaryType = 'blob';

	ws.addEventListener('open', () => {
		onOpen?.();
	});

	ws.addEventListener('message', (event) => {
		try {
			const data = JSON.parse(event.data as string) as PredictResponse | { error: string };
			if ('error' in data) {
				onError(data.error);
			} else {
				onMessage(data);
			}
		} catch {
			onError('Received malformed response from server.');
		}
	});

	ws.addEventListener('error', () => {
		onError('WebSocket connection error. Is the backend running?');
	});

	ws.addEventListener('close', () => {
		onClose?.();
	});

	return {
		sendFrame(blob: Blob) {
			if (ws.readyState === WebSocket.OPEN) {
				ws.send(blob);
			}
		},
		close() {
			if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
				ws.close(1000, 'Client closed connection');
			}
		}
	};
}
