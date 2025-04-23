<!-- @component Code Block based on: https://shiki.style/ -->

<script module>
    import { createHighlighterCoreSync } from 'shiki/core';
    import { createJavaScriptRegexEngine } from 'shiki/engine/javascript';
    // Themes
    // https://shiki.style/themes
    import themeDarkPlus from 'shiki/themes/dark-plus.mjs';
    // Languages
    // https://shiki.style/languages
    import json from 'shiki/langs/json.mjs';
    import console from 'shiki/langs/console.mjs';
    
    // https://shiki.style/guide/sync-usage
    const shiki = createHighlighterCoreSync({
        engine: createJavaScriptRegexEngine(),
        // Implement your import theme.
        themes: [themeDarkPlus],
        // Implement your imported and supported languages.
        langs: [json, console]
    });
</script>

<script lang="ts">
    import type { CodeBlockProps } from './types';
    
    let {
        code = '',
        lang = 'console',
        theme = 'dark-plus',
        // Base Style Props
        base = 'overflow-y-auto overflow-x-hidden',
        rounded = 'rounded-container',
        shadow = '',
        classes = 'text-left break-words',
        // Text Size Prop - newly added
        textSize = 'text-base',
        // Pre Style Props
        preBase = '[&>pre]:whitespace-pre-wrap [&>pre]:overflow-x-hidden',
        prePadding = '[&>pre]:p-4',
        preClasses = '[&>pre]:break-words [&>pre]:break-all [&>.shiki]:break-words [&>.shiki]:overflow-x-hidden',
        // Code Style Props
        codeClasses = '[&_code]:inline-block [&_code]:max-w-full [&_code]:break-all'
    }: CodeBlockProps = $props();
    
    // Shiki convert to HTML
    const generatedHtml = shiki.codeToHtml(code, { lang, theme });
</script>

<div class="{base} {rounded} {shadow} {classes} {textSize} {preBase} {prePadding} {preClasses} {codeClasses}">
    <!-- Output Shiki's Generated HTML -->
    {@html generatedHtml}
</div>