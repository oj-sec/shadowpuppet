<script lang="ts">
    
    import { onMount } from "svelte";
    import { ProgressRing } from "@skeletonlabs/skeleton-svelte";
    import ShadowPuppet from "$lib/ShadowPuppet.svelte";

    let loaded = $state(false);
    let data: any = $state({});
    let labels: any = $state({});
    
    onMount(async() => {
        const response = await fetch('/api/visualise/get-coordinates', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const responseData = await response.json();
        data = responseData.coordinates;
        loaded = true;
    });
    
    
</script>

<div class="w-full h-[92vh]">
    {#if loaded}
    <ShadowPuppet data={data}/>
    {:else}
    <div class="flex justify-center items-center w-full h-full my-16">
        <ProgressRing value={null} size="size-28" meterStroke="stroke-primary-600-400" trackStroke="stroke-primary-50-950" />
    </div>
    {/if} 
</div>
