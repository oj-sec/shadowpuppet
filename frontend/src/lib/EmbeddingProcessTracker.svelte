<script lang="ts">
    import { onMount } from "svelte";
    import { Progress } from '@skeletonlabs/skeleton-svelte';
    
    let { embeddingsCompleted = $bindable(false) } = $props();
    
    let embeddingStarted = $state(false);
    let totalDocuments = $state(0);
    let completedDocuments = $state(0);
    let remainingDocuments = $derived(totalDocuments - completedDocuments);
    let percentCompleted = $derived(Math.floor(completedDocuments / totalDocuments * 100));
    let documentsPerMinute = $state(0);
    let estimatedSecondsRemaining = $state(0);
    let estimatedParsedTimeRemaining = $derived(formatTimeRemaining(estimatedSecondsRemaining));
    let startTime = $state(Date.now());
    
    $effect(() => {
        if (completedDocuments > 0 && totalDocuments > 0) {
            documentsPerMinute = Math.floor((completedDocuments / (Date.now() - startTime)) * 60 * 1000);
            estimatedSecondsRemaining = Math.floor((remainingDocuments / documentsPerMinute) * 60);
        }
    });
    
    onMount(async () => {
        const response = await fetch("/api/database/total-documents");
        if (response.ok) {
            const data = await response.json();
            totalDocuments = data.totalDocuments;
        } else {
            console.error("Failed to fetch total documents");
        }
    });
    
    async function startEmbedding() {
        embeddingStarted = true;
        const response = await fetch("/api/embedding/queue-embeddings", {
            method: "POST",
        });
        const responseJson = await response.json();
        console.log(responseJson);
    }
    
    async function progressWatcherFunction() {
        setInterval(async () => {
            if (!embeddingStarted || embeddingsCompleted) {
                return;
            }
            const response = await fetch('/api/embeddings/check-progress');
            const responseJson = await response.json();
            completedDocuments = responseJson.completedDocuments;
            if (completedDocuments >= totalDocuments) {
                embeddingStarted = true;
                embeddingsCompleted = true;
            }
        }, 1500); 
    }
    
    progressWatcherFunction();
    
    function formatTimeRemaining(seconds: number): string {
        if (seconds == 0) {
            return "";
        } else if (seconds < 60) {
            return `${seconds} seconds${seconds === 1 ? '' : 's'}`;
        } else if (seconds < 3600) {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            return `${minutes} minute${minutes === 1 ? '' : 's'}${remainingSeconds > 0 ? ` ${remainingSeconds} second${remainingSeconds === 1 ? '' : 's'}` : ''}`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const remainingMinutes = Math.floor((seconds % 3600) / 60);
            return `${hours} hour${hours === 1 ? '' : 's'}${remainingMinutes > 0 ? ` ${remainingMinutes} minute${remainingMinutes === 1 ? '' : 's'}` : ''}`;
        }
    }    
    
</script>


<h2 class="h3 m-2">Generate embeddings</h2>
<div class="m-4">
    <Progress value={completedDocuments} max={totalDocuments}>{percentCompleted}%</Progress>
</div>  
<div>
    <div class="table-wrap">
        <table class="table caption-bottom">
            <tbody class="[&>tr]:hover:preset-tonal-primary">
                <tr>
                    <td class="text-left">Total documents:</td>
                    <td class="text-right">{totalDocuments}</td>
                </tr>
                <tr>
                    <td class="text-left">Completed documents:</td>
                    <td class="text-right">{completedDocuments}</td>
                </tr>
                <tr>
                    <td class="text-left">Documents per minute:</td>
                    <td class="text-right">{documentsPerMinute}</td>
                </tr>
                <tr>
                    <td class="text-left">Estimated time remaining:</td>
                    <td class="text-right">{estimatedParsedTimeRemaining}</td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
<button disabled={embeddingStarted} onclick={startEmbedding} type="button" class="btn mt-2 preset-filled">
    <span>Start</span>
</button>