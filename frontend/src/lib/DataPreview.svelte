<script>
    import { onMount } from "svelte";
    import CodeBlock from "$lib/CodeBlock.svelte";
    import { ProgressRing } from "@skeletonlabs/skeleton-svelte";
    
    let loaded = $state(false);
    let preveiwData = $state(null);
    
    onMount(async () => {
        const response = await fetch("/api/database/preview");
        const data = await response.json();
        if (!response.ok) {
            console.error("Failed to fetch data preview.");
            return;
        }
        preveiwData = data;
        loaded = true;
    });
    
</script>

{#if loaded}
<div class="overflow-auto">
    <CodeBlock code={JSON.stringify(preveiwData, null, 4)} lang="json" base="max-h-[40vh] overflow-y-auto overflow-x-hidden" />
</div>
{:else}
<div class="flex justify-center items-center w-full h-full my-16">
    <ProgressRing value={null} size="size-28" meterStroke="stroke-primary-600-400" trackStroke="stroke-primary-50-950" />
</div>
{/if}