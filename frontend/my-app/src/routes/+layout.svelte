<script lang="ts">
	import '../app.css';
	import BackendStatus from '$lib/components/BackendStatus.svelte';
	let { children } = $props();
</script>

<BackendStatus />
{@render children()}
