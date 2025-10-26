<script lang="ts">
    
    let {
        data,
        labels = null,
    } = $props();
    
    import { Graph } from "@cosmograph/cosmos";
    import { browser } from "$app/environment";
    import { onMount } from "svelte";
    import { Tabs } from '@skeletonlabs/skeleton-svelte';
    import CodeBlock from "$lib/CodeBlock.svelte";
    import { ProgressRing } from "@skeletonlabs/skeleton-svelte";
    import { Lock, TextCursor } from "@lucide/svelte";
    import { CircleX } from "@lucide/svelte";
    import HighlightRules from "$lib/HighlightRules.svelte";
    import { CosmosLabels } from "$lib/CosmosLabels.ts";
    
    let graphReady = $state(false);
    let initialData = $state({});
    let points: number[] = $state([]);
    let focusPoint: number = $state(-1);
    let graph: Graph;
    let cosmosLabels: CosmosLabels;
    let pointIndexToLabel: Map<number, string>;
    let pointData = $state({});
    let pointDataLoading = $state(false);
    let toolbarTabGroup = $state('Data');
    let lockedField = $state('');
    let samplePoint = $state({});
    let labelField = $state('');
    let resizeObserver: ResizeObserver | undefined;
    
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
        
        if (!browser) return;
        if (graph) graph.destroy();
        
        const div = document.getElementById("graph");
        if (!div) return;
        
        const config = {
            disableSimulation: true,
            pointSize: 2,
            pointSizeScale: 1,
            fitViewPadding: 0.3,
            renderHoveredPointRing: true,
            hoveredPointRingColor: "white",
            disableAttribution: true,
            showFPSMonitor: false,
            pointColor: "#32009f",
            onClick: (pointIndex, pointPosition, event) => handleClick(pointIndex, pointPosition, event),
        };
        
        graph = new Graph(div, config);
        graph.setPointPositions(points);
        graph.render();
        
        if (labelField && samplePoint[labelField]) {
            setupLabels(div);
        }
    }
    
    onMount(async () => {
        initialData = data;
        samplePoint = await getPointData(0);
        pointData = {};
        initialiseGraph();
        graphReady = true;
    });
    
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
        return pointData;
    }
    
    function fitView (): void {
        graph.fitView()
    }
    
    function zoomToPoint(): void {
        if (focusPoint === -1) {
            return;
        }
        graph.zoomToPointByIndex(focusPoint, 700, 20, true);
    }
    
    function colourMapper(hex: string): Float32Array {        
        const r = parseInt(hex.slice(1, 3), 16) / 255;
        const g = parseInt(hex.slice(3, 5), 16) / 255;
        const b = parseInt(hex.slice(5, 7), 16) / 255;
        const a = hex.length === 9 ? parseInt(hex.slice(7, 9), 16) / 255 : 1.0;
        return new Float32Array([r, g, b, a]);
    }
    
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
        if (!graphReady || !graph) return;
        console.log("Global point colour updated", globalPointColour);
        setGlobalPointColour();
        refreshLabels();
    });
    
    let backgroundColour = $state('#222222');
    $effect(() => {
        if (!graphReady || !graph) return;
        console.log("Background colour updated", backgroundColour);
        
        graph.setConfig({ backgroundColor: backgroundColour });
        graph.render();
        
        console.log("Config set to", graph.config);
        refreshLabels();
    });
    
    let globalPointSize = $state(2);
    $effect(() => {
        if (!graphReady || !graph) return;
        
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
        refreshLabels();
    });
    
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
    
    let highlightRules = $state([]);
    function updateColours() {
        setGlobalPointColour();
        for (let i = highlightRules.length - 1; i >= 0; i--) {
            const rule = highlightRules[i];
            if (rule.points) {
                const points = rule.points;
                const colour = rule.colour;
                const adjustedPoints = points.map((point) => point - 1);
                setPointColourByIndexes(adjustedPoints, colour);
            } else if (rule.pointGroups) {
                const pointGroups = rule.pointGroups;
                for (const [colour, points] of Object.entries(pointGroups)) {
                    const adjustedPoints = points.map((point) => point - 1);
                    setPointColourByIndexes(adjustedPoints, colour);
                }
            }
        }
    }
    $effect(() => {
        if (!graphReady || !graph) return;
        console.log("Highlight rules updated", highlightRules);
        updateColours();
        refreshLabels();
    });
    
    
    function setupLabels(div: HTMLDivElement) {
        const canvas = div.querySelector("canvas") as HTMLCanvasElement;
        if (!canvas) return;
        
        const existingContainer = div.querySelector(".cosmos-labels-container");
        if (existingContainer) {
            existingContainer.remove();
        }
        
        const canvasParent = canvas.parentElement!;
        if (getComputedStyle(canvasParent).position === "static") {
            canvasParent.style.position = "relative";
        }
        
        const labelsDiv = document.createElement("div");
        labelsDiv.className = "cosmos-labels-container";
        labelsDiv.style.position = "absolute";
        labelsDiv.style.top = "0";
        labelsDiv.style.left = "0";
        labelsDiv.style.width = `${canvas.clientWidth}px`;
        labelsDiv.style.height = `${canvas.clientHeight}px`;
        labelsDiv.style.pointerEvents = "none";
        canvasParent.appendChild(labelsDiv);
        
        cosmosLabels = new CosmosLabels(labelsDiv, pointIndexToLabel);        
        const labelIndices = Array.from(pointIndexToLabel.keys());
        graph.trackPointPositionsByIndices(labelIndices);
        
        graph.setConfig({
            ...graph.config,
            onZoom: () => {
                if (cosmosLabels && graph) {
                    cosmosLabels.update(graph);
                }
            },
        });
        
        resizeObserver = new ResizeObserver(() => {
            labelsDiv.style.width = `${canvas.clientWidth}px`;
            labelsDiv.style.height = `${canvas.clientHeight}px`;
            if (cosmosLabels) {
                cosmosLabels.update(graph);
            }
        });
        resizeObserver.observe(canvas);
        
        cosmosLabels.update(graph);
    }
    
    async function fetchColumnValues(columnName: string) {
        if (!columnName) return;
        
        try {
            const response = await fetch("/api/visualise/get-column-values", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ column: columnName }),
            });
            
            if (!response.ok) {
                console.error("Failed to fetch column values:", response.statusText);
                return;
            }
            
            const data: Record<string, string> = await response.json();
            
            pointIndexToLabel = new Map();
            Object.entries(data).forEach(([id, value]) => {
                pointIndexToLabel.set(Number(id), String(value));
            });
            
            if (graph && cosmosLabels) {
                cosmosLabels.pointIndexToLabel = pointIndexToLabel;
                cosmosLabels.update(graph);
            }
        } catch (err) {
            console.error("Error fetching column values:", err);
        }
    }
    
    function clearLabels() {
        if (graph && pointIndexToLabel && pointIndexToLabel.size > 0) {
            const labelIndices = Array.from(pointIndexToLabel.keys());
            if (graph.untrackPointPositionsByIndices) {
                graph.untrackPointPositionsByIndices(labelIndices);
            }
        }
        
        if (resizeObserver) {
            resizeObserver.disconnect();
            resizeObserver = undefined;
        }
        
        if (cosmosLabels) {
            cosmosLabels.destroy();
            cosmosLabels = undefined;
        }
        
        const div = document.getElementById("graph");
        if (div) {
            const old = div.querySelector(".cosmos-labels-container");
            if (old) {
                old.remove();
            }
        }
        
        pointIndexToLabel = undefined;
    }
    
    function refreshLabels() {
        if (cosmosLabels && pointIndexToLabel && pointIndexToLabel.size > 0) {
            setTimeout(() => {
                const div = document.getElementById("graph");
                if (div && pointIndexToLabel && pointIndexToLabel.size > 0) {
                    const savedLabelData = new Map(pointIndexToLabel);
                    clearLabels();
                    pointIndexToLabel = savedLabelData;
                    setupLabels(div);
                }
            }, 50);
        }
    }
    
    $effect(() => {
        if (!graphReady || !graph) return;
        
        const div = document.getElementById("graph");
        if (!div) return;
        
        if (!labelField) {
            clearLabels();
            return;
        }
        
        clearLabels();
        
        fetchColumnValues(labelField).then(() => {
            if (pointIndexToLabel && pointIndexToLabel.size > 0) {
                setupLabels(div);
            }
        });
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
                        <div class="input-group grid-cols-[auto_1fr_auto] my-2">                            
                            {#if labelField}
                            <div class="ig-cell preset-tonal" onclick={() => {labelField = ''}}>
                                <CircleX size={16}/>
                            </div>
                            {:else}
                            <div class="ig-cell preset-tonal">
                                <TextCursor size={16}/>
                            </div>
                            {/if}
                            <select class="ig-select" bind:value={labelField}>
                                {#each Object.keys(samplePoint) as key}
                                <option value={key}>{key}</option>
                                {/each}
                            </select>
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
                                                    Base point color
                                                </td>
                                                <td>
                                                    <input class="input" type="color" bind:value={globalPointColour} />
                                                </td>
                                            </tr>
                                            <tr>
                                                <td>
                                                    Base point size
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