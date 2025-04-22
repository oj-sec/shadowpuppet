<script lang="ts">
	import '../app.css';
	let { children } = $props();
	
	import { AppBar } from '@skeletonlabs/skeleton-svelte';
	import House from '@lucide/svelte/icons/house';
	import Cable from '@lucide/svelte/icons/cable';
	import RefreshCwOff from '@lucide/svelte/icons/refresh-cw-off';
	
	import { ToastProvider } from '@skeletonlabs/skeleton-svelte';
	import { onMount, onDestroy } from 'svelte';
	
	let healthCheckInterval: number;
	let dbName: string | null = $state(null);
	let connectionLost: boolean = $state(false);
	let hasConnected: boolean = $state(false);
	
	async function checkDatabaseHealth() {
		try {
			const response = await fetch('/api/database/health');
			const responseJson = await response.json();
			if (responseJson.loaded) {
				dbName = responseJson.name;
				hasConnected = true;
				connectionLost = false;
			} else {
				dbName = null;
			}
		} catch (error) {
			connectionLost = true;
		}
	}
	
	onMount(() => {
		checkDatabaseHealth();
		healthCheckInterval = setInterval(checkDatabaseHealth, 10000);
	});
	
	onDestroy(() => {
		clearInterval(healthCheckInterval);
	});
</script>

<AppBar classes="relative h-[7vh] min-h-[3.5rem]">
	{#snippet lead()}
	<a href="/"><House size={24} /></a>
	{/snippet}
	{#snippet trail()}
	{#if connectionLost && hasConnected && dbName}
		<span class="chip preset-tonal-error"><RefreshCwOff />{dbName}</span>
	{:else if dbName}
	<span class="chip preset-tonal-success"><Cable />{dbName}</span>
	{/if}
	{/snippet}
	<span class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none">
		shadowpuppet
	</span>
</AppBar>
<ToastProvider>
	{@render children()}
</ToastProvider>