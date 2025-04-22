<script lang="ts">
    
    import IconArrowLeft from '@lucide/svelte/icons/arrow-left';
    import IconArrowRight from '@lucide/svelte/icons/arrow-right';
    
    const steps = [
    { label: 'Step 1', description: '' },
    { label: 'Step 2', description: '' },
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
    import DbSelector from '$lib/DbSelector.svelte';
    let dbSelected: Boolean = $state(false);
    $effect(() => {
        if (dbSelected) {
            completedSteps = [...new Set([...completedSteps, currentStep])];
        }
    });

    // Step Two Functionality
    import ProjectionConfig from '$lib/ProjectionConfig.svelte';
    let projectionConfigured: Boolean = $state(false);
    $effect(() => {
        if (projectionConfigured) {
            completedSteps = [...new Set([...completedSteps, currentStep])];
        }
    });

    // Finish Functionality
    async function finish() {
        window.location.href = '/scatter';
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
                <DbSelector bind:dbSelected={dbSelected} />
            </div>
            {:else if i === 1}
            <div class="card bg-surface-100-900 p-8 space-y-2 text-center">
                <ProjectionConfig bind:projectionConfigured={projectionConfigured} />
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
                <button type="button" class="btn preset-tonal hover:preset-filled" onclick={finish} disabled={!projectionConfigured}>
                    <span>Visualise</span>
                    <IconArrowRight size={18} />
                </button>
                {/if}
            </nav>
        </div>
    </div>
</div>
</div>
