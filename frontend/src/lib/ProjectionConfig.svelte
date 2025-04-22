<script lang="ts">
    
    let { projectionConfigured = $bindable(false) } = $props();
    
    import { Tabs } from '@skeletonlabs/skeleton-svelte';
    import { Tooltip } from '@skeletonlabs/skeleton-svelte';
    import Info from '@lucide/svelte/icons/info';
    import { ProgressRing } from '@skeletonlabs/skeleton-svelte';
    import { getContext } from 'svelte';
    import { type ToastContext } from '@skeletonlabs/skeleton-svelte';
    export const toast: ToastContext = getContext('toast');
    
    let group = $state('PaCMAP');
    
    let nNeighboursToolTipOpenState = $state(false);
    let nNeighbours = $state(0);
    let initialisationMethod = $state('pca');
    let nearNeighbourRatio = $state(0.5);
    let farNeighbourRatio = $state(2);
    
    let validationInProgress = $state(false);
    let projectionRunning = $state(false);
    
    async function validate() {
        let invalidInput = false;
        validationInProgress = true;
        if (nNeighbours < 0) {
            invalidInput = true;
        } else if (initialisationMethod !== 'pca' && initialisationMethod !== 'random') {
            invalidInput = true;
        } else if (nearNeighbourRatio < 0) {
            invalidInput = true;
        } else if (farNeighbourRatio < 0) {
            invalidInput = true;
        }
        if (invalidInput) {
            toast.create({
                title: 'Error',
                description: 'Invalid input.',
                type: 'error'
            });
            validationInProgress = false;
            return;
        }
        
        const response = await fetch('/api/dimension-reduction/configure', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nNeighbours,
                initialisationMethod,
                nearNeighbourRatio,
                farNeighbourRatio
            })
        });
        
        const data = await response.json();
        if (response.ok) {
            runProjection();
        } else {
            toast.create({
                title: 'Error',
                description: "Error configuring projection.",
                type: 'error'
            });
        }
        validationInProgress = false;
    }
    
    async function runProjection() {
        projectionRunning = true;
        const response = await fetch('/api/dimension-reduction/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }
    
    async function progressWatcherFunction() {
        setInterval(async () => {
            if (!projectionRunning || projectionConfigured) {
                return;
            }
            const response = await fetch('/api/dimension-reduction/check-progress');
            const responseJson = await response.json();
            console.log(responseJson);
            if (responseJson.status === "success") {
                projectionRunning = false;
                projectionConfigured = true;
                toast.create({
                    title: 'Success',
                    description: "Projection completed.",
                    type: 'success'
                });
            } 
        }, 1000); 
    }
    
    progressWatcherFunction();
    
</script>


<h2 class="h3 m-2 mb-4">Reduce dimensions</h2>


<Tabs value={group} onValueChange={(e) => (group = e.value)} fluid>
    {#snippet list()}
    <Tabs.Control value="PaCMAP">PaCMAP</Tabs.Control>
    {/snippet}
    {#snippet content()}
    <Tabs.Panel value="PaCMAP"> 
        <div class="grid grid-cols-2 gap-4 m-4">
            <div>
                <label class="label">
                    <span class="label-text"><Tooltip
                        open={nNeighboursToolTipOpenState}
                        onOpenChange={(e) => (nNeighboursToolTipOpenState = e.open)}
                        positioning={{ placement: 'top' }}
                        triggerBase="hover:underline inline-flex items-center"
                        contentBase="card preset-filled p-4"
                        openDelay={200}
                        arrow
                        >
                        {#snippet trigger()}Number of neighbours <Info size={12}/>{/snippet}
                        {#snippet content()}Enter 0 to select automatically{/snippet}
                    </Tooltip></span>
                    <input class="input" type="number" placeholder="" bind:value={nNeighbours}/>
                </label>
            </div>
            <div>
                <label class="label">
                    <span class="label-text">Initialisation method</span>
                    <select class="select" bind:value={initialisationMethod}>
                        {#each ["pca", "random"] as method}
                        <option value={method}>{method}</option>
                        {/each}
                    </select>
                </label>
            </div>
            <div>
                <label class="label">
                    <span class="label-text">Near-neighbour ratio</span>
                    <input class="input" type="number" placeholder="" bind:value={nearNeighbourRatio}/>
                </label>
            </div>
            <div>
                <label class="label">
                    <span class="label-text">Far-neighbour ratio</span>
                    <input class="input" type="number" placeholder="" bind:value={farNeighbourRatio}/>
                </label>
            </div>
        </div>  
    </Tabs.Panel>
    {/snippet}
</Tabs>

<div class="w-full items-center text-center">
    {#if validationInProgress || projectionRunning}
    <button onclick={validate} disabled={validationInProgress || projectionRunning} type="button" class="btn mt-2 preset-filled min-w-[6rem]">
        <span><ProgressRing value={null} size="size-6" meterStroke="stroke-primary-600-400" trackStroke="stroke-primary-50-950" />
        </span>
    </button>
    {:else}
    <button onclick={validate} disabled={validationInProgress || projectionRunning || projectionConfigured} type="button" class="btn mt-2 preset-filled min-w-[6rem]">
        <span>Run</span>
    </button>
    {/if}
</div>