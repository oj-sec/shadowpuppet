<script lang="ts">
    
    let {
        highlightRules = $bindable([]),
    } = $props();
    
    import { CirclePlus } from "@lucide/svelte";
    import { X } from "@lucide/svelte";
    import { Modal } from '@skeletonlabs/skeleton-svelte';
    import { onMount } from "svelte";
    
    let columnOptions: string[] = $state([]);
    let selectedField: string = $state("");
    let selectedOperator: string = $state("contains");
    let query: string = $state("");
    let selectedColour: string = $state("#000000");
    let idTicker: number = $state(0);
    
    onMount(async () => {
        const response = await fetch('/api/database/columns');
        const responseJson = await response.json();
        responseJson.forEach((column: string) => {
            columnOptions.push(column);
        });
    });
    
    let modalOpenState = $state(false);
    let canConfrimModal = $state(false);
    function modalClose() {
        selectedField = "";
        selectedOperator = "contains";
        query = "";
        selectedColour = "#000000";
        modalOpenState = false;
    }
    
    $effect(() => {
        canConfrimModal = selectedField !== "" && query !== "";
    });
    
    async function modalConfirm() {
        const points = await queryForPointsMatching(query, selectedOperator);
        const rule = {
            ruleId: idTicker,
            field: selectedField,
            operator: selectedOperator,
            query: query,
            colour: selectedColour,
            points: points,
        };
        highlightRules.push(rule);
        highlightRules = [...highlightRules];
        idTicker++;
        modalClose();
    }
    
    async function queryForPointsMatching(query: string, operator: string): Promise<number[]> {
        const request = await fetch("/api/visualise/simple-query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                field: selectedField,
                query: query,
                operator: operator,
            }),
        })
        const response = await request.json();
        return response;
    }
    
    function addRule() {
        selectedField = "";
        selectedOperator = "contains";
        query = "";
        selectedColour = "#000000";
        modalOpenState = true;
    }
    
    function removeRule(id: number) {
        highlightRules = highlightRules.filter((rule) => rule.ruleId !== id);
        highlightRules = [...highlightRules];
    }
    
    // Drag and drop functionality
    import Dnd from '$lib/Dnd.svelte'
    function onSaveBasicList(e) {
        highlightRules = e
    }
    
</script>

<Modal
open={modalOpenState}
closeOnInteractOutside={false}
onOpenChange={(e) => (modalOpenState = e.open)}
triggerBase="btn preset-tonal"
contentBase="card bg-surface-100-900 p-4 space-y-4 shadow-xl min-w-[700px] max-w-4xl"
backdropClasses="backdrop-blur-sm"
>
{#snippet content()}
<header class="flex justify-between">
    <div class="w-full text-center">
        <h4 class="h4">Add highlight rule</h4>
    </div>
</header>
<article>
    <div class="flex flex-row gap-4 mt-4">
        <div class="flex flex-col">
            <label for="field" class="text-sm mb-1">Field</label>
            <select id="field" class="select min-w-[150px]" bind:value={selectedField}>
                {#each columnOptions as option}
                <option value={option}>{option}</option>
                {/each}
            </select>
        </div>
        
        <div class="flex flex-col">
            <label for="operator" class="text-sm mb-1">Operator</label>
            <select id="operator" class="select min-w-[150px]" bind:value={selectedOperator}>
                <option value="contains">contains</option>
                <option value="equals">equals</option>
                <option value="not contains">does not contain</option>
                <option value="not equals">does not equal</option>
            </select>
        </div>
        
        <div class="flex flex-col flex-grow">
            <label for="query" class="text-sm mb-1">Query</label>
            <input type="text" id="query" class="input min-w-[150px] w-full" bind:value={query} />
        </div>
        
        <div class="flex flex-col">
            <label class="text-sm mb-1">Colour</label>
            <input class="input w-16" type="color" bind:value={selectedColour} />
        </div>
    </div>
</article>
<footer class="flex justify-end gap-4">
    <button type="button" class="btn preset-tonal" onclick={modalClose}>Cancel</button>
    <button disabled={!canConfrimModal} type="button" class="btn preset-filled" onclick={modalConfirm}>Confirm</button>
</footer>
{/snippet}
</Modal>


<div class="max-h-[350px] overflow-y-auto">
    <div class="flex justify-center w-full px-2">
        <Dnd
        listName="highlight-rules"
        items={highlightRules}
        onFinalize={(e) => onSaveBasicList(e)}
        group="basic-list"
        itemClass="w-full text-center items-center"
        class="w-full text-center items-center"
        >
        {#snippet children(item)}
        <div style="width: 100%;" class="my-2 card card-hover w-full preset-filled-surface-100-900 p-4 border-gray-400 relative flex items-center">
            <div class="flex-1 text-center">
                <span class="break-words inline-block">
                    {item.field}: {item.operator === "equals" ? "=" :
                    item.operator === "not equals" ? "!=" : 
                    item.operator === "contains" ? "*" : 
                    item.operator === "not contains" ? "!*" : ""} 
                    "{item.query.length > 35 ? item.query.substring(0, 30) + "..." : item.query}"
                    <span
                    class="inline-block w-4 h-4 ml-1 align-middle rounded-full"
                    style="background-color: {item.colour};"
                    ></span>
                </span>
            </div>
            <button
            class="absolute top-1 right-1 hover:text-red-300"
            onclick={() => {
                removeRule(item.ruleId);
            }}
            >
            <X size={12} />
        </button>
    </div>
    
    {/snippet}
</Dnd>
</div>
</div>
<div class="flex justify-center w-full px-2">
    <div 
    onclick={addRule}
    class="card card-hover w-full preset-filled-surface-100-900 p-4 flex justify-center items-center border-2 border-dashed border-gray-400 my-2"
    >
    <i class="text-gray-500 text-2xl"><CirclePlus /></i>
</div>
</div>