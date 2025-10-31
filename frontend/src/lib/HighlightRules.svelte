<script lang="ts">
    let { highlightRules = $bindable([]) } = $props();

    import { CirclePlus } from "@lucide/svelte";
    import { X } from "@lucide/svelte";
    import { Modal } from "@skeletonlabs/skeleton-svelte";
    import { onMount } from "svelte";
    import { Tabs } from "@skeletonlabs/skeleton-svelte";
    import { hexToHSL, hslToHex } from "$lib/colourOperations.js";
    import { ProgressRing } from "@skeletonlabs/skeleton-svelte";
    import { getContext } from "svelte";
    import { type ToastContext } from "@skeletonlabs/skeleton-svelte";

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
    let queryLoading = $state(false);
    export const toast: ToastContext = getContext("toast");

    onMount(async () => {
        const response = await fetch("/api/database/columns");
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
        queryLoading = false;
    }

    $effect(() => {
        canConfrimModal = selectedField !== "" && maximumBuckets !== 0;
    });

    async function modalConfirm() {
        queryLoading = true;
        if (group === "Query") {
            const points = await queryForPointsMatching(
                query,
                selectedOperator,
                selectedField,
            );
            if (points === null) {
                queryLoading = false;
                return;
            }
            const rule = {
                ruleId: idTicker,
                field: selectedField,
                operator: selectedOperator,
                query: query,
                colour: selectedColour,
                points: points,
                type: "query",
            };
            highlightRules.push(rule);
            highlightRules = [...highlightRules];
            idTicker++;
            modalClose();
        } else if (group === "Sequential") {
            const pointGroups = await buildSequential(
                selectedField,
                maximumBuckets,
            );
            if (pointGroups === null) {
                queryLoading = false;
                return;
            }
            const colours = interpolateColours(
                startColour,
                endColour,
                maximumBuckets,
            );
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
                buckets: maximumBuckets,
            };
            highlightRules.push(rule);
            highlightRules = [...highlightRules];
            idTicker++;
            modalClose();
        } else if (group === "Category") {
            const pointGroups = await buildCategorical(
                selectedField,
                maximumBuckets,
            );
            if (pointGroups === null) {
                queryLoading = false;
                return;
            }
            const colours = interpolateColours(
                startColour,
                endColour,
                maximumBuckets,
            );
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
                buckets: maximumBuckets,
            };
            highlightRules.push(rule);
            highlightRules = [...highlightRules];
            idTicker++;
            modalClose();
        }
        queryLoading = false;
    }

    // Query handlers
    function triggerErrorToast() {
        console.log("Triggering error toast");
        toast.create({
            title: "Error",
            description: "Unable to execute query",
            type: "error",
            baseClasses: "bg-red-500 text-white",
        });
    }

    async function queryForPointsMatching(
        query: string,
        operator: string,
        field: string,
    ): Promise<number[] | null> {
        try {
            const request = await fetch("/api/visualise/simple-query", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    field: field,
                    query: query,
                    operator: operator,
                }),
            });

            if (!request.ok) {
                const errorText = await request
                    .text()
                    .catch(() => "Unknown error");
                triggerErrorToast();
                return null;
            }

            const response = await request.json();
            return response;
        } catch (error) {
            triggerErrorToast();
            return null;
        }
    }

    async function buildSequential(
        field: string,
        buckets: number | null,
    ): Promise<number[] | null> {
        try {
            const request = await fetch("/api/visualise/sequential-query", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    field: field,
                    buckets: buckets,
                }),
            });

            if (!request.ok) {
                const errorText = await request
                    .text()
                    .catch(() => "Unknown error");
                triggerErrorToast();
                return null;
            }

            const response = await request.json();
            return response;
        } catch (error) {
            triggerErrorToast();
            return null;
        }
    }

    async function buildCategorical(
        field: string,
        buckets: number | null,
    ): Promise<number[] | null> {
        try {
            const request = await fetch("/api/visualise/categorical-query", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    field: field,
                    buckets: buckets,
                }),
            });

            if (!request.ok) {
                const errorText = await request
                    .text()
                    .catch(() => "Unknown error");
                triggerErrorToast();
                return null;
            }

            const response = await request.json();
            return response;
        } catch (error) {
            triggerErrorToast();
            return null;
        }
    }

    function interpolateColours(startColour, endColour, steps) {
        if (steps === 1) return [startColour];
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
        queryLoading = false;
    }

    function removeRule(id: number) {
        highlightRules = highlightRules.filter((rule) => rule.ruleId !== id);
        highlightRules = [...highlightRules];
    }

    // Drag and drop functionality
    import Dnd from "$lib/Dnd.svelte";
    function onSaveBasicList(e) {
        highlightRules = e;
    }

    // Rule load and save functionality
    function downloadRules() {
        try {
            const cleanRules = highlightRules.map((rule) => ({
                ruleId: rule.ruleId,
                field: rule.field,
                operator: rule.operator,
                query: rule.query,
                colour: rule.colour,
                type: rule.type,
                startColour: rule.startColour ?? null,
                endColour: rule.endColour ?? null,
                buckets: rule.buckets ?? null,
            }));

            const blob = new Blob([JSON.stringify(cleanRules, null, 2)], {
                type: "application/json",
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "highlight-rules.json";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (err) {
            toast.create({
                title: "Error",
                description: "Unable to download rules.",
                type: "error",
            });
        }
    }

    async function uploadRules(event: Event) {
        const input = event.target as HTMLInputElement;
        const file = input.files?.[0];
        if (!file) return;

        queryLoading = true;

        try {
            const text = await file.text();
            const data: typeof highlightRules = JSON.parse(text);

            if (!Array.isArray(data)) throw new Error("Invalid file format");

            const rehydratedRules = [];
            const skippedRules = [];

            for (let i = 0; i < data.length; i++) {
                const rule = data[i];

                if (!columnOptions.includes(rule.field)) {
                    console.warn(
                        `Skipping rule ${rule.ruleId}: field "${rule.field}" does not exist`,
                    );
                    skippedRules.push(rule.field);
                    continue;
                }

                let points: number[] | null = null;
                let pointGroups: Record<string, number[]> | null = null;

                if (rule.type === "sequential") {
                    const pointGroupsArray = await buildSequential(
                        rule.field,
                        rule.buckets,
                    );
                    if (!pointGroupsArray)
                        throw new Error(
                            `Sequential query failed for ruleId ${rule.ruleId}`,
                        );

                    const colours = interpolateColours(
                        rule.startColour,
                        rule.endColour,
                        rule.buckets,
                    );
                    const colourDict = {};
                    for (let j = 0; j < pointGroupsArray.length; j++) {
                        colourDict[colours[j]] = pointGroupsArray[j];
                    }
                    pointGroups = colourDict;
                } else if (rule.type === "categorical") {
                    const pointGroupsArray = await buildCategorical(
                        rule.field,
                        rule.buckets,
                    );
                    if (!pointGroupsArray)
                        throw new Error(
                            `Categorical query failed for ruleId ${rule.ruleId}`,
                        );

                    const colours = interpolateColours(
                        rule.startColour,
                        rule.endColour,
                        rule.buckets,
                    );
                    const colourDict = {};
                    for (let j = 0; j < pointGroupsArray.length; j++) {
                        colourDict[colours[j]] = pointGroupsArray[j];
                    }
                    pointGroups = colourDict;
                } else if (rule.type === "query") {
                    points = await queryForPointsMatching(
                        rule.query,
                        rule.operator,
                        rule.field,
                    );
                    if (points === null)
                        throw new Error(
                            `Query failed for ruleId ${rule.ruleId}`,
                        );
                }

                rehydratedRules.push({
                    ruleId:
                        typeof rule.ruleId === "number"
                            ? rule.ruleId
                            : idTicker++,
                    field: rule.field,
                    operator: rule.operator,
                    query: typeof rule.query === "string" ? rule.query : "",
                    colour:
                        typeof rule.colour === "string"
                            ? rule.colour
                            : "#000000",
                    type: typeof rule.type === "string" ? rule.type : "query",
                    startColour:
                        typeof rule.startColour === "string"
                            ? rule.startColour
                            : null,
                    endColour:
                        typeof rule.endColour === "string"
                            ? rule.endColour
                            : null,
                    buckets:
                        typeof rule.buckets === "number" ? rule.buckets : null,
                    points,
                    pointGroups,
                });
            }

            highlightRules = [...rehydratedRules];
            idTicker = rehydratedRules.length;

            if (rehydratedRules.length > 0 && skippedRules.length === 0) {
                toast.create({
                    title: "Rules imported",
                    description: `${rehydratedRules.length} rules loaded and rehydrated.`,
                    type: "success",
                });
            } else if (rehydratedRules.length > 0 && skippedRules.length > 0) {
                toast.create({
                    title: "Rules partially imported",
                    description: `${rehydratedRules.length} rules loaded. ${skippedRules.length} skipped due to missing fields: ${[...new Set(skippedRules)].join(", ")}`,
                    type: "warning",
                    baseClasses: "bg-yellow-500 text-white",
                });
            } else {
                toast.create({
                    title: "No rules imported",
                    description: `All rules skipped due to missing fields: ${[...new Set(skippedRules)].join(", ")}`,
                    type: "error",
                });
            }
        } catch (err) {
            toast.create({
                title: "Error",
                description:
                    "Failed to import rules: " + (err as Error).message,
                type: "error",
            });
        } finally {
            queryLoading = false;
            (event.target as HTMLInputElement).value = "";
        }
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
                            <i class="text-sm text-gray-500"
                                >Highlight points matching a simple query</i
                            >
                        </div>
                        <div class="flex flex-row gap-4 mt-4">
                            <div class="flex flex-col">
                                <label for="field" class="text-sm mb-1"
                                    >Field</label
                                >
                                <select
                                    id="field"
                                    class="select min-w-[150px]"
                                    bind:value={selectedField}
                                >
                                    {#each columnOptions as option}
                                        <option value={option}>{option}</option>
                                    {/each}
                                </select>
                            </div>

                            <div class="flex flex-col">
                                <label for="operator" class="text-sm mb-1"
                                    >Operator</label
                                >
                                <select
                                    id="operator"
                                    class="select min-w-[150px]"
                                    bind:value={selectedOperator}
                                >
                                    <option value="contains">contains</option>
                                    <option value="equals">equals</option>
                                    <option value="not contains"
                                        >does not contain</option
                                    >
                                    <option value="not equals"
                                        >does not equal</option
                                    >
                                </select>
                            </div>

                            <div class="flex flex-col flex-grow">
                                <label for="query" class="text-sm mb-1"
                                    >Query</label
                                >
                                <input
                                    type="text"
                                    id="query"
                                    class="input min-w-[150px] w-full"
                                    bind:value={query}
                                />
                            </div>

                            <div class="flex flex-col">
                                <label class="text-sm mb-1">Colour</label>
                                <input
                                    class="input w-16"
                                    type="color"
                                    bind:value={selectedColour}
                                />
                            </div>
                        </div>
                    </Tabs.Panel>
                    <Tabs.Panel value="Sequential">
                        <div class="w-full text-center items-center">
                            <i class="text-sm text-gray-500 max-w-2/3"
                                >Highlight points using up to 100 buckets
                                generated for a sequential field</i
                            >
                        </div>
                        <div
                            class="flex flex-row gap-4 mt-4 items-center justify-center"
                        >
                            <div class="flex flex-col">
                                <label for="field" class="text-sm mb-1"
                                    >Field</label
                                >
                                <select
                                    id="field"
                                    class="select min-w-[150px]"
                                    bind:value={selectedField}
                                >
                                    {#each columnOptions as option}
                                        <option value={option}>{option}</option>
                                    {/each}
                                </select>
                            </div>

                            <div class="flex flex-col">
                                <label for="operator" class="text-sm mb-1"
                                    >Buckets</label
                                >
                                <input
                                    type="number"
                                    step="1"
                                    min="2"
                                    max="100"
                                    class="input min-w-[150px]"
                                    bind:value={maximumBuckets}
                                />
                            </div>

                            <div class="flex flex-col">
                                <label class="text-sm mb-1">Start colour</label>
                                <input
                                    class="input w-16"
                                    type="color"
                                    bind:value={startColour}
                                />
                            </div>

                            <div class="flex flex-col">
                                <label class="text-sm mb-1">End colour</label>
                                <input
                                    class="input w-16"
                                    type="color"
                                    bind:value={endColour}
                                />
                            </div>
                        </div>
                    </Tabs.Panel>
                    <Tabs.Panel value="Category">
                        <div class="w-full text-center items-center">
                            <i class="text-sm text-gray-500 max-w-2/3"
                                >Highlight points using up to 100 unique values
                                for a field, sorted by most represented</i
                            >
                        </div>
                        <div
                            class="flex flex-row gap-4 mt-4 items-center justify-center"
                        >
                            <div class="flex flex-col">
                                <label for="field" class="text-sm mb-1"
                                    >Field</label
                                >
                                <select
                                    id="field"
                                    class="select min-w-[150px]"
                                    bind:value={selectedField}
                                >
                                    {#each columnOptions as option}
                                        <option value={option}>{option}</option>
                                    {/each}
                                </select>
                            </div>

                            <div class="flex flex-col">
                                <label for="operator" class="text-sm mb-1"
                                    >Buckets</label
                                >
                                <input
                                    type="number"
                                    step="1"
                                    min="2"
                                    max="100"
                                    class="input min-w-[150px]"
                                    bind:value={maximumBuckets}
                                />
                            </div>

                            <div class="flex flex-col">
                                <label class="text-sm mb-1">Start colour</label>
                                <input
                                    class="input w-16"
                                    type="color"
                                    bind:value={startColour}
                                />
                            </div>

                            <div class="flex flex-col">
                                <label class="text-sm mb-1">End Colour</label>
                                <input
                                    class="input w-16"
                                    type="color"
                                    bind:value={endColour}
                                />
                            </div>
                        </div></Tabs.Panel
                    >
                {/snippet}
            </Tabs>
        </article>
        <footer class="flex justify-end gap-4">
            <button type="button" class="btn preset-tonal" onclick={modalClose}
                >Cancel</button
            >
            {#if queryLoading}
                <button
                    type="button"
                    class="btn preset-filled px-8"
                    onclick={modalClose}
                    ><span
                        ><ProgressRing
                            value={null}
                            size="size-6"
                            meterStroke="stroke-primary-600-400"
                            trackStroke="stroke-primary-50-950"
                        />
                    </span>
                </button>
            {:else}
                <button
                    disabled={!canConfrimModal}
                    type="button"
                    class="btn preset-filled"
                    onclick={modalConfirm}>Confirm</button
                >
            {/if}
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
                <div
                    class="my-2 card card-hover w-full preset-filled-surface-100-900 p-4 border-gray-400 relative flex items-center"
                >
                    <div class="flex-1 text-center">
                        {#if item.points}
                            <span class="break-words inline-block">
                                {item.field}: {item.operator === "equals"
                                    ? "="
                                    : item.operator === "not equals"
                                      ? "!="
                                      : item.operator === "contains"
                                        ? "*"
                                        : item.operator === "not contains"
                                          ? "!*"
                                          : ""}
                                "{item.query.length > 35
                                    ? item.query.substring(0, 30) + "..."
                                    : item.query}"
                                <span
                                    class="inline-block w-4 h-4 ml-1 align-middle rounded-full"
                                    style="background-color: {item.colour};"
                                ></span>
                            </span>
                        {:else if item.pointGroups}
                            <span class="break-words inline-block">
                                {item.field}: {item.type === "sequential"
                                    ? "[...]"
                                    : "{...}"}
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
<div class="flex flex-col w-full px-2 space-y-2 mt-2">
    <div
        onclick={addRule}
        class="card card-hover w-full preset-filled-surface-100-900 p-4 flex justify-center items-center border-2 border-dashed border-gray-400"
    >
        <i class="text-gray-500 text-2xl"><CirclePlus /></i>
    </div>

    <label class="btn preset-tonal w-full cursor-pointer text-center">
        Upload Rules
        <input
            type="file"
            accept="application/json"
            onchange={uploadRules}
            class="hidden"
        />
    </label>

    {#if highlightRules.length > 0}
        <button
            type="button"
            class="btn preset-tonal w-full"
            onclick={downloadRules}
        >
            Download Rules
        </button>
    {/if}
</div>
