<script lang="ts">
    
    let {
        data,
    } = $props();
    
    import { Graph } from "@cosmograph/cosmos";
    import { browser } from "$app/environment";
    import { onMount } from "svelte";
    import { Tabs } from '@skeletonlabs/skeleton-svelte';
    import CodeBlock from "$lib/CodeBlock.svelte";
    import { ProgressRing } from "@skeletonlabs/skeleton-svelte";
    import { Lock } from "@lucide/svelte";
    import { CircleX } from "@lucide/svelte";
    import HighlightRules from "$lib/HighlightRules.svelte";
    
    let initialData = $state({});
    let points: number[] = $state([]);
    let focusPoint: number = $state(-1);
    let graph: Graph;
    let pointData = $state({});
    let pointDataLoading = $state(false);
    let toolbarTabGroup = $state('Data');
    let lockedField = $state('');
    
    function handleClick(pointIndex: number | undefined, pointPosition: [number, number], event: MouseEvent | undefined) {
        if (pointIndex) {
            setPointHilight(pointIndex);
            getPointData(pointIndex);
            toolbarTabGroup = 'Data';
        } 
    }
    
    function setPointHilight(pointIndex: number) {
        if (focusPoint === pointIndex) {
            focusPoint = -1;
            graph.setFocusedPointByIndex(undefined);
            return;
        }
        focusPoint = pointIndex;
        graph.setFocusedPointByIndex(pointIndex);
    }
    
    function initialiseGraph() {
        points = Object.values(initialData).flat();
        if (browser) {
            if (graph) {
                graph.destroy();
            }
            const div = document.getElementById("graph");
            const config = {
                disableSimulation: true,
                pointSize: 4,
                pointSizeScale: 0.5,
                fitViewPadding: 0.3,
                renderHoveredPointRing: true,
                hoveredPointRingColor: "white",
                disableAttribution: true,
                showFPSMonitor: false,
                pointColor: "#32009f",
                onClick: (pointIndex, pointPosition, event) => {
                    handleClick(pointIndex, pointPosition, event);
                }
            };
            
            graph = new Graph(div, config);
            graph.setPointPositions(points);
            graph.render();
            console.log(graph);
        }
    }
    
    onMount(() => {
        initialData = data;
        initialiseGraph();
    });
    
    // Point data viewer
    async function getPointData(pointIndex: number) {
        pointDataLoading = true;
        pointData = {};
        const request = await fetch("/api/visualise/get-point", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                id: pointIndex + 1,
            }),
        })
        const response = await request.json();
        pointData = response;
        pointData = pointData;
        pointDataLoading = false;
    }
    
    // Fit view
    function fitView (): void {
        graph.fitView()
    }
    
    // Zoom to point
    function zoomToPoint(): void {
        if (focusPoint === -1) {
            return;
        }
        graph.zoomToPointByIndex(focusPoint, 700, 20, true);
    }
    
    // Colour mapper 
    function colourMapper(hex: string): Float32Array {        
        const r = parseInt(hex.slice(1, 3), 16) / 255;
        const g = parseInt(hex.slice(3, 5), 16) / 255;
        const b = parseInt(hex.slice(5, 7), 16) / 255;
        const a = hex.length === 9 ? parseInt(hex.slice(7, 9), 16) / 255 : 1.0;
        return new Float32Array([r, g, b, a]);
    }
    
    // Set global point colour
    let globalPointColour = $state("#32009f");
    function setGlobalPointColour() {
        const numPoints = points.length / 2;
        const globalPointColourArray = new Float32Array(numPoints * 4);
        const colour = colourMapper(globalPointColour);
        for (let i = 0; i < numPoints; i++) {
            globalPointColourArray[i * 4] = colour[0];    
            globalPointColourArray[i * 4 + 1] = colour[1]; 
            globalPointColourArray[i * 4 + 2] = colour[2]; 
            globalPointColourArray[i * 4 + 3] = colour[3]; 
        }
        graph.setPointColors(globalPointColourArray);
        graph.render();
    }
    $effect(() => {
        console.log("Global point colour updated", globalPointColour);
        setGlobalPointColour();
    });
    
    // Set background colour
    let backgroundColour = $state('#222222');
    $effect(() => {
        console.log("Background colour updated", backgroundColour);
        let currentConfig = { ...graph.config };
        currentConfig.backgroundColor = backgroundColour;
        console.log("Setting config to", currentConfig);
        graph.setConfig(currentConfig);
        graph.render();
        console.log("Config set to", graph.config);
    });
    
    // Set global point size
    let globalPointSize = $state(4);
    $effect(() => {
        if (globalPointSize < 1 || globalPointSize % 1 !== 0) {
            return
        }
        const numPoints = points.length / 2;
        const globalPointSizeArray = new Float32Array(numPoints);
        for (let i = 0; i < numPoints; i++) {
            globalPointSizeArray[i] = globalPointSize;
        }
        graph.setPointSizes(globalPointSizeArray);
        graph.render();
    });
    
    // Function to set point colour by indexes
    function setPointColourByIndexes(indexes: number[], colour: string): void {
        const currentColourArray = graph.points.data.pointColors;
        const colourArray = colourMapper(colour);
        const newColourArray = currentColourArray.slice();
        let ticker = 0
        for (let i = 0; i < indexes.length; i++) {
            const index = indexes[i] * 4;
            ticker++;
            newColourArray[index] = colourArray[0];
            newColourArray[index + 1] = colourArray[1];
            newColourArray[index + 2] = colourArray[2];
            newColourArray[index + 3] = colourArray[3];
        }
        graph.setPointColors(newColourArray);
        graph.render();
    }
    
    // Highlight rules functionality
    let highlightRules = $state([]);
    function updateColours() {
        setGlobalPointColour();
        for (let i = highlightRules.length - 1; i >= 0; i--) {
            const rule = highlightRules[i];
            const points = rule.points;
            const colour = rule.colour;
            // Address the off-by-one error in the points array
            const adjustedPoints = points.map((point) => point - 1);
            setPointColourByIndexes(adjustedPoints, colour);
        }
    }
    $effect(() => {
        console.log("Highlight rules updated", highlightRules);
        updateColours();
    });
    
</script>

<div class="h-full w-full">
    <div class="grid grid-cols-5 h-full">
        <div class="p-1">
            <Tabs value={toolbarTabGroup} onValueChange={(e) => (toolbarTabGroup = e.value)} fluid>
                {#snippet list()}
                <Tabs.Control value="Data">Data</Tabs.Control>
                <Tabs.Control value="Toolbox">Toolbox</Tabs.Control>
                {/snippet}
                {#snippet content()}
                <Tabs.Panel value="Data">
                    <div class="h-full overflow-auto m-2">
                        {#if pointData && Object.keys(pointData).length > 0}
                        <div class="input-group grid-cols-[auto_1fr_auto] mb-2">                            
                            {#if lockedField}
                            <div class="ig-cell preset-tonal" onclick={() => {lockedField = ''}}>
                                <CircleX size={16}/>
                            </div>
                            {:else}
                            <div class="ig-cell preset-tonal">
                                <Lock size={16}/>
                            </div>
                            {/if}
                            <select class="ig-select" bind:value={lockedField}>
                                {#each Object.keys(pointData) as key}
                                <option value={key}>{key}</option>
                                {/each}
                            </select>
                        </div>
                        {#if lockedField}
                        {#key lockedField}
                        <CodeBlock code={JSON.stringify(pointData[lockedField], null, 2)} textSize="text-xs max-h-[70vh] overflow-y-auto overflow-x-hidden" lang="json" />
                        {/key}
                        {:else}
                        <CodeBlock code={JSON.stringify(pointData, null, 2)} textSize="text-xs max-h-[70vh] overflow-y-auto overflow-x-hidden" lang="json" />
                        {/if}
                        {:else if pointDataLoading}
                        <div class="flex justify-center items-center w-full h-full my-48">
                            <ProgressRing value={null} size="size-14" meterStroke="stroke-primary-600-400" trackStroke="stroke-primary-50-950" />
                        </div>
                        {:else}
                        <div class="flex justify-center items-center w-full h-full my-16">
                            <p class="text-gray-500">Click on a point to view data</p>
                        </div>
                        {/if}
                    </div> 
                </Tabs.Panel>
                <Tabs.Panel value="Toolbox">
                    <div class="h-full overflow-auto m-2">
                        <div class="grid grid-cols-2 gap-1">
                            <button type="button" class="btn preset-tonal hover:preset-filled" onclick={fitView}>
                                Fit view
                            </button>
                            <button type="button" disabled={focusPoint === -1 ? true : false} class="btn preset-tonal hover:preset-filled" onclick={zoomToPoint}>
                                Zoom to point
                            </button>
                        </div>
                        <div class="w-full">
                            <div class="m-2 flex justify-center">
                                <div class="table-wrap">
                                    <table class="table">
                                        <tbody class="">
                                            <tr>
                                                <td>
                                                    Background colour
                                                </td>
                                                <td>
                                                    <input class="input" type="color" bind:value={backgroundColour} />
                                                </td>
                                            </tr>
                                            <tr>
                                                <td>
                                                    Global point color
                                                </td>
                                                <td>
                                                    <input class="input" type="color" bind:value={globalPointColour} />
                                                </td>
                                            </tr>
                                            <tr>
                                                <td>
                                                    Global point size
                                                </td>
                                                <td>
                                                    <input 
                                                    class="input w-16" 
                                                    type="number" 
                                                    min="1" 
                                                    step="1"
                                                    bind:value={globalPointSize} 
                                                    />
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                        <div class="card w-full max-w-md preset-outlined-surface-100-900 p-2 text-center">
                            <h6 class="h6">Highlight rules</h6>
                            <HighlightRules bind:highlightRules={highlightRules} />
                        </div>
                    </Tabs.Panel>
                    {/snippet}
                </Tabs>
            </div>
            <div class="col-span-4">
                <div id="graph" class="h-full w-full overflow-hidden"></div>
            </div>
        </div>
    </div>
    
    