<script lang="ts">
    import { onMount } from 'svelte';
    import { ProgressRing } from '@skeletonlabs/skeleton-svelte';
    
    let { dbSelected = $bindable(false) } = $props();
    let loaded = $state(false);
    let dbData = $state(null);
    let selectedDb = $state(null);
    let selectedTable = $state(null);
    let selectedColumn = $state(null);
    
    import { getContext } from 'svelte';
    import { type ToastContext } from '@skeletonlabs/skeleton-svelte';
    export const toast: ToastContext = getContext('toast');
    
    function createToast(title: string, message: string, type: "error" | "success" | "info" | undefined) {
        toast.create({
            title: title,
            description: message,
            type: type
        });    
    }
    
    onMount(async () => {
        const response = await fetch('/api/visualise/list-databases', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await response.json();
        if (response.ok) {
            if (data.selectedDatabase !== null) {
                const preSelectedDb = data.databases.find(db => db.name === data.selectedDatabase);
                if (preSelectedDb) {
                    const otherDbs = data.databases.filter(db => db.name !== data.selectedDatabase);
                    dbData = [preSelectedDb, ...otherDbs];
                    selectedDb = preSelectedDb;
                } else {
                    dbData = data.databases;
                    selectedDb = null;
                }
            } else {
                dbData = data.databases;
                selectedDb = null;
            }
            loaded = true;
        } else {
            console.error('Error fetching databases:', data.message);
        }
    });
    
    function selectDb(db) {
        selectedDb = db;
        selectedTable = null;
        selectedColumn = null;
    }
    
    function selectTable(tableName) {
        selectedTable = tableName;
        selectedColumn = null;
    }
    
    function selectColumn(columnName) {
        selectedColumn = columnName;
    }
    
    $effect(() => {
        if (selectedDb && selectedTable && selectedColumn) {
            console.log(`Selected: ${selectedDb.name}, table: ${selectedTable}, column: ${selectedColumn}`);
        }
    });
    
    async function selectDatabase() {
        if (!selectedDb) {
            createToast('Warning', 'Select a database first.', 'warning');
            return;
        }
        const response = await fetch('/api/database/select-database', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                database: selectedDb.name,
            })
        });
        const data = await response.json();
        if (response.ok) {
            dbSelected = true;
            createToast('Success', `Database selected successfully.`, 'success');
        } else {
            createToast('Error', 'Error selecting database.', 'error');
        }
    }
</script>

<h2 class="h3 m-2 mb-4">Select database</h2>
{#if loaded}
<div class="flex flex-row gap-1 w-full border rounded">
    <div class="flex-1 flex flex-col">
        <h3 class="text-sm font-semibold p-2 bg-surface-500 border-b text-center">Databases</h3>
        <div class="overflow-y-auto h-60">
            <ul class="space-y-1 p-2">
                {#each dbData as db}
                <li 
                class="p-2 rounded cursor-pointer hover:bg-primary-100 transition-colors" 
                class:bg-primary-200={selectedDb && selectedDb.name === db.name}
                on:click={() => selectDb(db)}
                >
                {db.name}
            </li>
            {/each}
        </ul>
    </div>
</div>

<!-- Tables Column -->
<div class="flex-1 flex flex-col border-l">
    <h3 class="text-sm font-semibold p-2 bg-surface-500 border-b text-center">Tables</h3>
    <div class="overflow-y-auto h-60">
        {#if selectedDb}
        <ul class="space-y-1 p-2">
            {#each Object.keys(selectedDb.tables) as tableName}
            <li 
            class="p-2 rounded cursor-pointer hover:bg-primary-100 transition-colors"
            class:bg-primary-200={selectedTable === tableName}
            on:click={() => selectTable(tableName)}
            >
            <div>{tableName}</div>
            <div class="text-xs text-secondary-200">{selectedDb.tables[tableName].row_count} rows</div>
        </li>
        {/each}
    </ul>
    {:else}
    <p class="text-sm text-secondary-200 italic p-4">Select a database first</p>
    {/if}
</div>
</div>

<!-- Columns Column -->
<div class="flex-1 flex flex-col border-l">
    <h3 class="text-sm font-semibold p-2 bg-surface-500 border-b text-center">Columns</h3>
    <div class="overflow-y-auto h-60">
        {#if selectedDb && selectedTable}
        <ul class="space-y-1 p-2">
            {#each selectedDb.tables[selectedTable].columns as columnName}
            <li 
            class="p-2 rounded cursor-pointer hover:bg-primary-100 transition-colors"
            class:bg-primary-200={selectedColumn === columnName}
            on:click={() => selectColumn(columnName)}
            >
            {columnName}
        </li>
        {/each}
    </ul>
    {:else}
    <p class="text-sm text-secondary-200 italic p-4">Select a table first</p>
    {/if}
</div>
</div>
</div>
<div class="w-full items-center text-center">
    <button on:click={selectDatabase} type="button" class="btn mt-2 preset-filled min-w-[6rem]">
        <span>Select</span>
    </button>
</div>
{:else}
<div class="flex justify-center items-center w-full h-full my-16">
    <ProgressRing value={null} size="size-28" meterStroke="stroke-primary-600-400" trackStroke="stroke-primary-50-950" />
</div>
{/if}