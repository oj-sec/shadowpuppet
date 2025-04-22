<script lang="ts">
  let { embeddingsConfigured = $bindable(false) } = $props();
  import { onMount } from 'svelte';
  import { Tooltip } from '@skeletonlabs/skeleton-svelte';
  import Info from '@lucide/svelte/icons/info';
  import { getContext } from 'svelte';
  import { type ToastContext } from '@skeletonlabs/skeleton-svelte';
  import { Modal } from '@skeletonlabs/skeleton-svelte';
  import { ProgressRing } from '@skeletonlabs/skeleton-svelte';
  
  export const toast: ToastContext = getContext('toast');
  
  let openState = $state(false);
  let logOutput: HTMLPreElement | null = null;
  let logBuffer = $state("");
  
  let embeddingModelToolTipOpenState = $state(false);
  let overflowToolTipOpenState = $state(false);
  let embeddingInstructionToolTipOpenState = $state(false);
  let dimnensionReductionToolTipOpenState = $state(false);
  
  onMount(async () => {
    const response = await fetch('/api/database/columns');
    const responseJson = await response.json();
    responseJson.forEach((column: string) => {
      columnOptions.push(column);
    });
  });
  
  const columnOptions: string[] = $state([]);    
  const overflowStrategyOptions: string[] = [
  "truncate",
  "pool"
  ];
  
  // Data fields
  let selectedColumn: string = $state("");
  let embeddingModel: string = $state("mixedbread-ai/mxbai-embed-large-v1");
  let overflowStrategy: string = $state("truncate");
  let dimensionTruncation: number | null = $state(null);
  let embeddingInstruction: string = $state("");  
  
  // Validation
  let validationInProgress = $state(false);
  async function validate() {
    validationInProgress = true;
    if (!selectedColumn || !embeddingModel || !overflowStrategy) {
      toast.create({
        title: 'Error',
        description: 'Complete all required fields.',
        type: 'error'
      });
      validationInProgress = false;
      return;
    }
    
    const response = await fetch('/api/embeddings/configure', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        selectedColumn,
        embeddingModel,
        overflowStrategy,
        dimensionTruncation,
        embeddingInstruction
      })
    });
    
    const responseJson = await response.json();
    if (responseJson.status === 'success') {
      toast.create({
        title: 'Success',
        description: 'Embeddings configured successfully.',
        type: 'success'
      });
      embeddingsConfigured = true;
      validationInProgress = false;
      return
    } else if (responseJson.status === 'pending') {
      logBuffer = responseJson.logs;
      openState = true;
    } else {
      toast.create({
        title: 'Error',
        description: "Error configuring embeddings.",
        type: 'error'
      });
    }
    validationInProgress = false;
  }
  
  async function downloadWatcherFunction() {
    setInterval(async () => {
      if (!openState) {
        return;
      }
      const response = await fetch('/api/embeddings/check-download');
      const responseJson = await response.json();
      if (responseJson.modelObject != "None") {
        toast.create({
          title: 'Success',
          description: `Model downloaded successfully.`,
          type: 'success'
        });
        embeddingsConfigured = true;
        openState = false;
        return;
      }
      logBuffer = responseJson.logs;
      if (logOutput) {
        console.log("scrolling")
        console.log(logOutput.scrollTop, logOutput.scrollHeight)
        logOutput.scrollTop = logOutput.scrollHeight;
      } 
    }, 5000); 
  }
  
  downloadWatcherFunction();
  
</script>



<Modal
open={openState}
onOpenChange={(e) => (openState = e.open)}
triggerBase="btn preset-tonal"
contentBase="card bg-surface-100-900 p-4 space-y-4 shadow-xl max-w-1/2"
backdropClasses="backdrop-blur-sm"
closeOnInteractOutside={false}
closeOnEscape={false}
>
{#snippet content()}
<header class="flex justify-between">
  <h2 class="h4">Please wait - model downloading</h2>
</header>
<article class="max-h-[50vh] overflow-y-auto overflow-x-auto">
  {#if logBuffer}
  <pre bind:this={logOutput} class="whitespace-pre overflow-x-auto font-mono text-xs p-2 bg-surface-200-800 rounded">
    {logBuffer.trimStart()}
  </pre>
  {:else}
  <div class="placeholder animate-pulse"></div>
  {/if}
</article>
<footer class="flex justify-end gap-4">
</footer>
{/snippet}
</Modal>


<h2 class="h3 m-2">Configure embeddings</h2>

<div class="grid grid-cols-2 gap-4 m-4">
  
  <div>
    
    <label class="label">
      <span class="label-text">Embedding field</span>
      <select class="select" bind:value={selectedColumn}>
        {#each columnOptions as column}
        <option value={column}>{column}</option>
        {/each}
      </select>
    </label>
    
  </div>
  <div>
    <label class="label">
      <span class="label-text"><Tooltip
        open={embeddingModelToolTipOpenState}
        onOpenChange={(e) => (embeddingModelToolTipOpenState = e.open)}
        positioning={{ placement: 'top' }}
        triggerBase="hover:underline inline-flex items-center"
        contentBase="card preset-filled p-4"
        openDelay={200}
        arrow
        >
        {#snippet trigger()}Embedding model  <Info size={12}/>{/snippet}
        {#snippet content()}Enter a sentence-transformers compatible embedding model HuggingFace repository.{/snippet}
      </Tooltip></span>
      <input class="input" type="text" placeholder="Input..." bind:value={embeddingModel}/>
    </label>
  </div>
  
  <div>
    
    <label class="label">
      <span class="label-text"><Tooltip
        open={overflowToolTipOpenState}
        onOpenChange={(e) => (overflowToolTipOpenState = e.open)}
        positioning={{ placement: 'top' }}
        triggerBase="hover:underline inline-flex items-center"
        contentBase="card preset-filled p-4"
        openDelay={200}
        arrow
        >
        {#snippet trigger()}Overflow strategy <Info size={12}/>{/snippet}
        {#snippet content()}Select a stragegy to handle input values that overflow the embedding model's max sequence length.{/snippet}
      </Tooltip></span>
      <select class="select" disabled bind:value={overflowStrategy}>
        {#each overflowStrategyOptions as strategy}
        <option value={strategy}>{strategy}</option>
        {/each}
      </select>
    </label>
    
  </div>
  
  <div>
    
    <label class="label">
      <span class="label-text"><Tooltip
        open={dimnensionReductionToolTipOpenState}
        onOpenChange={(e) => (dimnensionReductionToolTipOpenState = e.open)}
        positioning={{ placement: 'top' }}
        triggerBase="hover:underline inline-flex items-center"
        contentBase="card preset-filled p-4"
        openDelay={200}
        arrow
        >
        {#snippet trigger()}Truncate output dimensions <Info size={12}/>{/snippet}
        {#snippet content()}Truncate the model's output vectors to a lower dimension count or leave blank.{/snippet}
      </Tooltip></span>
      <input class="input" type="number" placeholder="" bind:value={dimensionTruncation}/>
    </label>
    
  </div>
  
  <div class="col-span-2">
    <label class="label">
      <span class="label-text"><Tooltip
        open={embeddingInstructionToolTipOpenState}
        onOpenChange={(e) => (embeddingInstructionToolTipOpenState = e.open)}
        positioning={{ placement: 'top' }}
        triggerBase="hover:underline inline-flex items-center"
        contentBase="card preset-filled p-4"
        openDelay={200}
        arrow
        >
        {#snippet trigger()}Embedding instruction <Info size={12}/>{/snippet}
        {#snippet content()}The instruction to prepend to passages for embeddng. Use the instruction provided in model documentation or leave blank.{/snippet}
      </Tooltip></span>
      <textarea class="textarea" rows="2" placeholder="Enter instruction..." bind:value={embeddingInstruction}></textarea>
    </label>
  </div>
  
</div>

<div class="w-full items-center text-center">
  {#if validationInProgress}
  <button onclick={validate} disabled={validationInProgress} type="button" class="btn mt-2 preset-filled min-w-[6rem]">
    <span><ProgressRing value={null} size="size-7" meterStroke="stroke-primary-600-400" trackStroke="stroke-primary-50-950" />
    </span>
  </button>
  {:else}
  <button onclick={validate} disabled={validationInProgress} type="button" class="btn mt-2 preset-filled min-w-[6rem]">
    <span>Validate</span>
  </button>
  {/if}
</div>

