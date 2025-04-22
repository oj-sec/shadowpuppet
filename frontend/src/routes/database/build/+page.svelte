<script lang="ts">
    import IconArrowLeft from '@lucide/svelte/icons/arrow-left';
    import IconArrowRight from '@lucide/svelte/icons/arrow-right';
    
    // Generic Functionality
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
    
    // Stepper Functionality
    const steps = [
    { label: 'Step 1', description: '' },
    { label: 'Step 2', description: '' },
    { label: 'Step 3', description: '' },
    { label: 'Step 4', description: '' },
    ];
    
    let currentStep = $state(0);
    let completedSteps = $state([1]);
    let isNextDisabled = $state(true);
    const isFirstStep = $derived(currentStep === 0);
    const isLastStep = $derived(currentStep === steps.length - 1);
    
    $effect(() => {
        if (completedSteps.includes(currentStep)) {
            isNextDisabled = false;
        } else {
            isNextDisabled = true;
        }
        isNextDisabled = isNextDisabled;
    });
    
    function isCurrentStep(index: number) {
        return currentStep === index;
    }
    
    function prevStep() {
        currentStep--;
    }
    
    function nextStep() {
        currentStep++;
    }
    
    // Step One Functionality
    
    import { FileUpload } from '@skeletonlabs/skeleton-svelte';
    import IconDropzone from '@lucide/svelte/icons/image-plus';
    import IconFile from '@lucide/svelte/icons/paperclip';
    import IconRemove from '@lucide/svelte/icons/circle-x';
    
    let fileObject: File | null = $state(null);
    let isFileSelected = $state(false);
    function handleFileChange(event: any) {
        const file = event.acceptedFiles[0];
        if (!file)  {
            fileObject = null;
            return;
        } else {
            fileObject = file;
        }
    }
    
    $effect(() => {
        if (fileObject == null) {
            isFileSelected = false;
        } else {
            isFileSelected = true;
        }
    });
    
    async function uploadFile() {
        const formData = new FormData();
        formData.append('file', fileObject);
        const response = await fetch('/api/database/upload-file', {
            method: 'POST',
            body: formData
        });
        if (response.ok) {
            createToast("Success", "File uploaded successfully.", "success");
            completedSteps = [...new Set([...completedSteps, currentStep])];
        } else {
            createToast("Error", "Failed to upload file.", "error");
        }
    }
    
    // Step Two Functionality
    import DataPreview from '$lib/DataPreview.svelte';
    
    // Step Three Functionality
    import EmbeddingConfig from '$lib/EmbeddingConfig.svelte';
    let embeddingsConfigured = $state(false);
    $effect(() => {
        if (embeddingsConfigured) {
            completedSteps = [...new Set([...completedSteps, currentStep])];
        }
    });
    
    // Step Four Functionality
    import EmbeddingProcessTracker from '$lib/EmbeddingProcessTracker.svelte';
    let embeddingsCompleted = $state(false);
    $effect(() => {
        if (embeddingsCompleted) {
            completedSteps = [...new Set([...completedSteps, currentStep])];
        }
    });
    
    function finish() {
        window.location.href = '/';
    }
    
</script>


<div class="w-full h-[92vh] flex justify-center items-center">
    <div class="w-1/2">
        <div class="w-full">
            <div class="space-y-8">
                <div class="relative">
                    <div class="flex justify-between items-center gap-4">
                        {#each steps as step, i}
                        <button
                        class="btn-icon btn-icon-sm rounded-full {isCurrentStep(i) ? 'preset-filled-primary-500' : 'preset-filled-surface-200-800'}"
                        title={step.label}
                        >
                        <span class="font-bold">{i + 1}</span>
                    </button>
                    {/each}
                </div>
                <hr class="hr !border-surface-200-800 absolute top-[50%] left-0 right-0 z-[-1]" />
            </div>
            {#each steps as step, i (step)}
            {#if isCurrentStep(i)}
            {#if i === 0}
            <div class="card bg-surface-100-900 p-8 space-y-2 text-center">
                <h2 class="h3 m-2">Load data</h2>
                <FileUpload
                name="example"
                accept={[".csv",".json", ".ndjson"]}
                maxFiles={1}
                subtext="CSV, JSON and ndJSON files allowed"
                onFileChange={handleFileChange}
                onFileReject={() => createToast("Error", "Invalid file type.", "error")}
                classes="w-full"
                >
                {#snippet iconInterface()}<IconDropzone class="size-8" />{/snippet}
                {#snippet iconFile()}<IconFile class="size-4" />{/snippet}
                {#snippet iconFileRemove()}<IconRemove class="size-4" />{/snippet}
            </FileUpload>
            <button disabled={!isFileSelected} onclick={uploadFile} type="button" class="btn mt-2 preset-filled">
                <span>Upload</span>
            </div>
            {:else if i === 1}
            <div class="card bg-surface-100-900 p-8 space-y-2 text-center max-h-[60vh] flex flex-col">
                <h2 class="h3 m-2">Preview data</h2>
                <div class="overflow-y-auto flex-grow">
                    <DataPreview />
                </div>
            </div>
            {:else if i === 2}
            <div class="card bg-surface-100-900 p-8 space-y-2 text-center">
                <EmbeddingConfig bind:embeddingsConfigured={embeddingsConfigured}/>                
            </div>
            {:else if i === 3}
            <div class="card bg-surface-100-900 p-8 space-y-2 text-center items-center">
                <EmbeddingProcessTracker bind:embeddingsCompleted={embeddingsCompleted} />
            </div>
            {/if}
            {/if}
            {/each}
            <nav class="flex justify-between items-center gap-4">
                <button type="button" class="btn preset-tonal hover:preset-filled" onclick={prevStep} disabled={isFirstStep}>
                    <IconArrowLeft size={18} />
                    <span>Previous</span>
                </button>
                {#if !isLastStep}
                <button type="button" class="btn preset-tonal hover:preset-filled" onclick={nextStep} disabled={isNextDisabled}>
                    <span>Next</span>
                    <IconArrowRight size={18} />
                </button>
                {:else}
                <button type="button" class="btn preset-tonal hover:preset-filled" onclick={finish} disabled={!embeddingsCompleted}>
                    <span>Finish</span>
                    <IconArrowRight size={18} />
                </button>
                {/if}
            </nav>
        </div>
    </div>
</div>
</div>