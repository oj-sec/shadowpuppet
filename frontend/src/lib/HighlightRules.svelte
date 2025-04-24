<script lang="ts">
    
    let {
        highlightRules = $bindable([]),
    } = $props();
    
    import { CirclePlus } from "@lucide/svelte";
    import { X } from "@lucide/svelte";
    import { Modal } from '@skeletonlabs/skeleton-svelte';
    import { onMount } from "svelte";
    import { Tabs } from "@skeletonlabs/skeleton-svelte";
    import { hexToHSL, hslToHex } from "$lib/colourOperations.js";
    
    let columnOptions: string[] = $state([]);
    let selectedField: string = $state("");
    let selectedOperator: string = $state("contains");
    let query: string = $state("");
    let selectedColour: string = $state("#000000");
    let startColour: string = $state("#000000");
    let endColour: string = $state("#000000");
    let maximumBuckets: number | null = $state(null);
    let idTicker: number = $state(0);
    let group = $state("Query");
    
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
        startColour = "#000000";
        endColour = "#000000";
        maximumBuckets = null;
        modalOpenState = false;
    }
    
    $effect(() => {
        canConfrimModal = selectedField !== "" && (maximumBuckets !== 0);
    });
    
    async function modalConfirm() {
        if (group === "Query") {
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
        } else if (group === "Sequential") {
            const pointGroups = await buildSequential(selectedField, maximumBuckets);
            const colours = interpolateColours(startColour, endColour, maximumBuckets);
            const colourDict = {};
            for (let i = 0; i < pointGroups.length; i++) {
                colourDict[colours[i]] = pointGroups[i];
            }
            const rule = {
                ruleId: idTicker,
                field: selectedField,
                operator: selectedOperator,
                query: query,
                colour: selectedColour,
                pointGroups: colourDict,
                type: "sequential",
                startColour: startColour,
                endColour: endColour,
            };
            highlightRules.push(rule);
            highlightRules = [...highlightRules];
            idTicker++;
            modalClose();
        } else if (group === "Category") {
            const pointGroups = await buildCategorical(selectedField, maximumBuckets);
            const colours = interpolateColours(startColour, endColour, maximumBuckets);
            const colourDict = {};
            for (let i = 0; i < pointGroups.length; i++) {
                colourDict[colours[i]] = pointGroups[i];
            }
            const rule = {
                ruleId: idTicker,
                field: selectedField,
                operator: selectedOperator,
                query: query,
                colour: selectedColour,
                pointGroups: colourDict,
                type: "categorical",
                startColour: startColour,
                endColour: endColour,
            };
            highlightRules.push(rule);
            highlightRules = [...highlightRules];
            idTicker++;
            modalClose();
        }
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
    
    async function buildSequential(field: string, buckets: number | null): Promise<number[]> {
        const request = await fetch("/api/visualise/sequentual-query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                field: field,
                buckets: buckets,
            }),
        })
        const response = await request.json();
        return response;
    }
    
    async function buildCategorical(field: string, buckets: number | null): Promise<number[]> {
        const request = await fetch("/api/visualise/categorical-query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                field: field,
                buckets: buckets,
            }),
        })
        const response = await request.json();
        return response;
    }
    
    
    function interpolateColours(startColour, endColour, steps) {
        const startHSL = hexToHSL(startColour);
        const endHSL = hexToHSL(endColour);
        
        const result = [];
        
        let hueDiff = endHSL.h - startHSL.h;
        if (Math.abs(hueDiff) > 180) {
            hueDiff = hueDiff > 0 ? hueDiff - 360 : hueDiff + 360;
        }
        
        for (let i = 0; i < steps; i++) {
            const ratio = i / (steps - 1);
            
            const h = (startHSL.h + ratio * hueDiff + 360) % 360; 
            const s = startHSL.s + ratio * (endHSL.s - startHSL.s);
            const l = startHSL.l + ratio * (endHSL.l - startHSL.l);
            
            result.push(hslToHex(h, s, l));
        }
        
        return result;
    }
    
    function addRule() {
        selectedField = "";
        selectedOperator = "contains";
        query = "";
        selectedColour = "#000000";
        startColour = "#000000";
        endColour = "#000000";
        maximumBuckets = null;
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
    <Tabs value={group} onValueChange={(e) => (group = e.value)} fluid>
        {#snippet list()}
        <Tabs.Control value="Query">Query</Tabs.Control>
        <Tabs.Control value="Sequential">Sequential</Tabs.Control>
        <Tabs.Control value="Category">Category</Tabs.Control>
        {/snippet}
        {#snippet content()}
        <Tabs.Panel value="Query"> 
            <div class="w-full text-center items-center">
                <i class="text-sm text-gray-500">Highlight points matching a simple query</i>
            </div>
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
        </Tabs.Panel>
        <Tabs.Panel value="Sequential"> 
            <div class="w-full text-center items-center">
                <i class="text-sm text-gray-500 max-w-2/3">Highlight points using up to 100 buckets generated for a sequential field</i>
            </div>
            <div class="flex flex-row gap-4 mt-4 items-center justify-center">
                <div class="flex flex-col">
                    <label for="field" class="text-sm mb-1">Field</label>
                    <select id="field" class="select min-w-[150px]" bind:value={selectedField}>
                        {#each columnOptions as option}
                        <option value={option}>{option}</option>
                        {/each}
                    </select>
                </div>
                
                <div class="flex flex-col">
                    <label for="operator" class="text-sm mb-1">Buckets</label>
                    <input type="number" step="1" min="2" max="100" class="input min-w-[150px]" bind:value={maximumBuckets} />
                </div>
                
                <div class="flex flex-col">
                    <label class="text-sm mb-1">Start colour</label>
                    <input class="input w-16" type="color" bind:value={startColour} />
                </div>
                
                <div class="flex flex-col">
                    <label class="text-sm mb-1">End Colour</label>
                    <input class="input w-16" type="color" bind:value={endColour} />
                </div>
            </div>
        </Tabs.Panel>
        <Tabs.Panel value="Category"> 
            <div class="w-full text-center items-center">
                <i class="text-sm text-gray-500 max-w-2/3">Highlight points using up to 100 unique values for a field, sorted by most represented</i>
            </div>
            <div class="flex flex-row gap-4 mt-4 items-center justify-center">
                <div class="flex flex-col">
                    <label for="field" class="text-sm mb-1">Field</label>
                    <select id="field" class="select min-w-[150px]" bind:value={selectedField}>
                        {#each columnOptions as option}
                        <option value={option}>{option}</option>
                        {/each}
                    </select>
                </div>
                
                <div class="flex flex-col">
                    <label for="operator" class="text-sm mb-1">Buckets</label>
                    <input type="number" step="1" min="2" max="100" class="input min-w-[150px]" bind:value={maximumBuckets} />
                </div>
                
                <div class="flex flex-col">
                    <label class="text-sm mb-1">Start colour</label>
                    <input class="input w-16" type="color" bind:value={startColour} />
                </div>
                
                <div class="flex flex-col">
                    <label class="text-sm mb-1">End Colour</label>
                    <input class="input w-16" type="color" bind:value={endColour} />
                </div>
            </Tabs.Panel>
            {/snippet}
        </Tabs>
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
        <div class="my-2 card card-hover w-full preset-filled-surface-100-900 p-4 border-gray-400 relative flex items-center">
            <div class="flex-1 text-center">
                {#if item.points}
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
                {:else if item.pointGroups}
                <span class="break-words inline-block">
                    {item.field}: {item.type === "sequential" ? "[...]" : "{...}"} 
                    <span
                    class="inline-block w-4 h-4 ml-1 align-middle rounded-full"
                    style="background-color: {item.startColour};"
                    ></span>
                    <span
                    class="inline-block w-4 h-4 ml-1 align-middle rounded-full"
                    style="background-color: {item.endColour};"
                    ></span>
                </span>
                {/if}
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