import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		allowedHosts: true, // Allow ngrok hosts to connect
		proxy: {
			// Proxy all /api HTTP requests to FastAPI during development.
			// WebSocket proxy is handled separately below.
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true
			},
			'/api/stream': {
				target: 'ws://localhost:8000',
				ws: true,
				changeOrigin: true
			}
		}
	}
});
