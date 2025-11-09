<script lang="ts">
    let { data, labels = null } = $props();

    import { Graph } from "@cosmograph/cosmos";
    import { browser } from "$app/environment";
    import { onMount } from "svelte";
    import { Tabs } from "@skeletonlabs/skeleton-svelte";
    import CodeBlock from "$lib/CodeBlock.svelte";
    import { ProgressRing } from "@skeletonlabs/skeleton-svelte";
    import { Lock, TextCursor, CircleX } from "@lucide/svelte";
    import HighlightRules from "$lib/HighlightRules.svelte";
    import { CosmosLabels } from "$lib/CosmosLabels.ts";
    import {
        hexToRGBA,
        createUniformColorArray,
        createUniformSizeArray,
        applyColorToIndices,
    } from "$lib/graphUtils.ts";

    // ============= STATE: GRAPH =============
    let graphReady = $state(false);
    let initialData = $state({});
    let points: number[] = $state([]);
    let focusPoint: number = $state(-1);
    let graph: Graph;

    // ============= STATE: LABELS =============
    let cosmosLabels: CosmosLabels;
    let pointIndexToLabel: Map<number, string>;
    let labelField = $state("");
    let resizeObserver: ResizeObserver | undefined;

    // ============= STATE: POINT DATA =============
    let pointData = $state({});
    let pointDataLoading = $state(false);
    let columns = $state([]);

    // ============= STATE: UI =============
    let toolbarTabGroup = $state("Data");
    let lockedField = $state("");

    // ============= STATE: APPEARANCE =============
    let globalPointColour = $state("#32009f");
    let backgroundColour = $state("#222222");
    let globalPointSize = $state(2);
    let highlightRules = $state([]);

    // ============= STATE: LINKS =============
    let currentLinks: Float32Array | null = $state(null);

    // ============= GRAPH FUNCTIONS =============

    function handleClick(
        pointIndex: number | undefined,
        pointPosition: [number, number],
        event: MouseEvent | undefined,
    ) {
        if (pointIndex === undefined) return;
        const wasFocused = focusPoint === pointIndex;
        setPointHilight(pointIndex);
        if (!wasFocused) {
            getPointData(pointIndex);
            toolbarTabGroup = "Data";
        }
    }

    function setPointHilight(pointIndex: number) {
        if (focusPoint === pointIndex) {
            focusPoint = -1;
            graph.setFocusedPointByIndex(undefined);
            pointData = {};
            clearLinks();
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
            focusedPointRingColor: "white",
            disableAttribution: true,
            showFPSMonitor: false,
            pointColor: "#32009f",
            curvedLinks: true,
            linkArrows: true,
            linkVisibilityDistanceRange: [0, 150],
            linkGreyoutOpacity: 1,
            linkColor: "#d6d2d2",
            onClick: (pointIndex, pointPosition, event) =>
                handleClick(pointIndex, pointPosition, event),
        };

        graph = new Graph(div, config);
        graph.setPointPositions(points);
        graph.render();
        refreshLabels();

        if (labelField && columns.includes(labelField)) {
            setupLabels(div);
        }
    }

    function fitView(): void {
        graph.fitView();
    }

    function zoomToPoint(): void {
        if (focusPoint === -1) {
            return;
        }
        graph.zoomToPointByIndex(focusPoint, 700, 20, true);
    }

    // ============= POINT DATA FUNCTIONS =============

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
        });
        const response = await request.json();
        pointData = response;
        pointDataLoading = false;

        drawNearestNeighborLinks(pointIndex);

        return pointData;
    }

    async function getColumns() {
        const response = await fetch("/api/database/columns");
        const responseJson = await response.json();
        responseJson.forEach((column: string) => {
            columns.push(column);
        });
    }

    // ============= LINK FUNCTIONS =============

    function drawNearestNeighborLinks(pointIndex: number) {
        if (!graph || !pointData._nearest_neighbours) {
            clearLinks();
            return;
        }

        try {
            const neighbors = JSON.parse(pointData._nearest_neighbours);

            if (!Array.isArray(neighbors) || neighbors.length === 0) {
                clearLinks();
                return;
            }

            const linksArray = new Float32Array(neighbors.length * 2);

            neighbors.forEach((neighborId: number, index: number) => {
                const neighborIndex = neighborId - 1;
                linksArray[index * 2] = pointIndex;
                linksArray[index * 2 + 1] = neighborIndex;
            });

            currentLinks = linksArray;
            graph.setLinks(linksArray);
            graph.render();
            refreshLabels();
        } catch (error) {
            console.error("Error parsing nearest neighbors:", error);
            clearLinks();
        }
    }

    function clearLinks() {
        if (graph && currentLinks) {
            graph.setLinks(new Float32Array([]));
            graph.render();
            refreshLabels();
            currentLinks = null;
        }
    }

    // ============= COLOR FUNCTIONS =============

    function setGlobalPointColour() {
        const numPoints = points.length / 2;
        const color = hexToRGBA(globalPointColour);
        const colorArray = createUniformColorArray(numPoints, color);
        graph.setPointColors(colorArray);
        graph.render();
    }

    function setPointColourByIndexes(
        indexes: number[],
        colourHex: string,
    ): void {
        const currentColors = graph.points.data.pointColors;
        const color = hexToRGBA(colourHex);
        const newColors = applyColorToIndices(currentColors, indexes, color);
        graph.setPointColors(newColors);
        graph.render();
    }

    function updateColours() {
        setGlobalPointColour();
        for (let i = highlightRules.length - 1; i >= 0; i--) {
            const rule = highlightRules[i];
            if (rule.points) {
                const adjustedPoints = rule.points.map((point) => point - 1);
                setPointColourByIndexes(adjustedPoints, rule.colour);
            } else if (rule.pointGroups) {
                for (const [colour, points] of Object.entries(
                    rule.pointGroups,
                )) {
                    const adjustedPoints = points.map((point) => point - 1);
                    setPointColourByIndexes(adjustedPoints, colour);
                }
            }
        }
    }

    // ============= LABEL FUNCTIONS =============

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
                console.error(
                    "Failed to fetch column values:",
                    response.statusText,
                );
                return;
            }

            const data: Record<string, string> = await response.json();

            pointIndexToLabel = new Map();
            Object.entries(data).forEach(([id, value]) => {
                pointIndexToLabel.set(Number(id) - 1, String(value));
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

    // ============= LIFECYCLE =============

    onMount(async () => {
        initialData = data;
        await getColumns();
        pointData = {};
        initialiseGraph();
        graphReady = true;
    });

    // ============= EFFECTS =============

    $effect(() => {
        if (!graphReady || !graph) return;
        setGlobalPointColour();
        refreshLabels();
    });

    $effect(() => {
        if (!graphReady || !graph) return;
        graph.setConfig({ backgroundColor: backgroundColour });
        graph.render();
        refreshLabels();
    });

    $effect(() => {
        if (!graphReady || !graph) return;

        if (globalPointSize < 1 || globalPointSize % 1 !== 0) {
            return;
        }
        const numPoints = points.length / 2;
        const sizeArray = createUniformSizeArray(numPoints, globalPointSize);
        graph.setPointSizes(sizeArray);
        graph.render();
        refreshLabels();
    });

    $effect(() => {
        if (!graphReady || !graph) return;
        updateColours();
        refreshLabels();
    });

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
            <Tabs
                value={toolbarTabGroup}
                onValueChange={(e) => (toolbarTabGroup = e.value)}
                fluid
            >
                {#snippet list()}
                    <Tabs.Control value="Data">Data</Tabs.Control>
                    <Tabs.Control value="Toolbox">Toolbox</Tabs.Control>
                {/snippet}
                {#snippet content()}
                    <Tabs.Panel value="Data">
                        <div class="h-full overflow-auto m-2">
                            {#if pointData && Object.keys(pointData).length > 0}
                                <div
                                    class="input-group grid-cols-[auto_1fr_auto] mb-2"
                                >
                                    {#if lockedField}
                                        <div
                                            class="ig-cell preset-tonal"
                                            onclick={() => {
                                                lockedField = "";
                                            }}
                                        >
                                            <CircleX size={16} />
                                        </div>
                                    {:else}
                                        <div class="ig-cell preset-tonal">
                                            <Lock size={16} />
                                        </div>
                                    {/if}
                                    <select
                                        class="ig-select"
                                        bind:value={lockedField}
                                    >
                                        {#each Object.keys(pointData) as key}
                                            <option value={key}>{key}</option>
                                        {/each}
                                    </select>
                                </div>
                                {#if lockedField}
                                    {#key lockedField}
                                        <CodeBlock
                                            code={JSON.stringify(
                                                pointData[lockedField],
                                                null,
                                                2,
                                            )}
                                            textSize="text-xs max-h-[70vh] overflow-y-auto overflow-x-hidden"
                                            lang="json"
                                        />
                                    {/key}
                                {:else}
                                    <CodeBlock
                                        code={JSON.stringify(
                                            pointData,
                                            null,
                                            2,
                                        )}
                                        textSize="text-xs max-h-[70vh] overflow-y-auto overflow-x-hidden"
                                        lang="json"
                                    />
                                {/if}
                            {:else if pointDataLoading}
                                <div
                                    class="flex justify-center items-center w-full h-full my-48"
                                >
                                    <ProgressRing
                                        value={null}
                                        size="size-14"
                                        meterStroke="stroke-primary-600-400"
                                        trackStroke="stroke-primary-50-950"
                                    />
                                </div>
                            {:else}
                                <div
                                    class="flex justify-center items-center w-full h-full my-16"
                                >
                                    <p class="text-gray-500">
                                        Click on a point to view data
                                    </p>
                                </div>
                            {/if}
                        </div>
                    </Tabs.Panel>
                    <Tabs.Panel value="Toolbox">
                        <div class="h-full overflow-auto m-2">
                            <div class="grid grid-cols-2 gap-1">
                                <button
                                    type="button"
                                    class="btn preset-tonal hover:preset-filled"
                                    onclick={fitView}
                                >
                                    Fit view
                                </button>
                                <button
                                    type="button"
                                    disabled={focusPoint === -1 ? true : false}
                                    class="btn preset-tonal hover:preset-filled"
                                    onclick={zoomToPoint}
                                >
                                    Zoom to point
                                </button>
                            </div>
                            <div
                                class="input-group grid-cols-[auto_1fr_auto] my-2"
                            >
                                {#if labelField}
                                    <div
                                        class="ig-cell preset-tonal"
                                        onclick={() => {
                                            labelField = "";
                                        }}
                                    >
                                        <CircleX size={16} />
                                    </div>
                                {:else}
                                    <div class="ig-cell preset-tonal">
                                        <TextCursor size={16} />
                                    </div>
                                {/if}
                                <select
                                    class="ig-select"
                                    bind:value={labelField}
                                >
                                    {#each columns as key}
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
                                                    <td> Background colour </td>
                                                    <td>
                                                        <input
                                                            class="input"
                                                            type="color"
                                                            bind:value={
                                                                backgroundColour
                                                            }
                                                        />
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td> Base point color </td>
                                                    <td>
                                                        <input
                                                            class="input"
                                                            type="color"
                                                            bind:value={
                                                                globalPointColour
                                                            }
                                                        />
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td> Base point size </td>
                                                    <td>
                                                        <input
                                                            class="input w-16"
                                                            type="number"
                                                            min="1"
                                                            step="1"
                                                            bind:value={
                                                                globalPointSize
                                                            }
                                                        />
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                            <div
                                class="card w-full max-w-md preset-outlined-surface-100-900 p-2 text-center"
                            >
                                <h6 class="h6">Highlight rules</h6>
                                <HighlightRules
                                    bind:highlightRules
                                    columnOptions={columns}
                                />
                            </div>
                        </div></Tabs.Panel
                    >
                {/snippet}
            </Tabs>
        </div>
        <div class="col-span-4">
            <div id="graph" class="h-full w-full overflow-hidden"></div>
        </div>
    </div>
</div>
