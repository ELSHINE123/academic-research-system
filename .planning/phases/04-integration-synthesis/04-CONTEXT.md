# Phase 4 Context: Integration & Synthesis

## Phase Goal
Bridge the gap between "Researching" and "Writing". Provide professional export tools and a synthesis engine that doesn't just "chat" but "cites".

## 1. Export Lounge (The "Exit Strategy")
**"Format-Agnostic Handover"**

*   **Word XML (Bibliography):** Ensure strict APA/MLA XML compliance for Microsoft Word's "Manage Sources" feature.
*   **Excel Matrix:** A structured review matrix including `Status`, `Methodology`, `Key Findings`, and `Impact Score`.
*   **Notion Sync:** A robust, one-way sync to a user-provided Notion Database ID. Map fields: Title -> Name, URL -> URL, Abstract -> Content, Status -> Status.

## 2. Advanced RAG Synthesis (The "Writer")
**"Mandatory Grounding"**

*   **Problem:** Current synthesis just answers from context.
*   **Solution:** **Strict Inline Citations**.
*   **Prompt Engineering:** Force Gemini to use `[Author, Year]` format for every claim.
*   **Source Linking:** If a citation is detected `[Smith, 2024]`, verify it exists in the active library.

## 3. UI Refinement
*   **Split-Screen Power:** Ensure the synthesis pane (Right) remains usable while navigating complex graphs or matrices on the Left.

## Technical Implementation (Planner Notes)
*   **Notion:** Use `requests` to hit Notion API `v1/pages`. Handle rate limits.
*   **RAG:** Upgrade prompt to include "Citation Rules".
*   **Exports:** Use `openpyxl` for better Excel formatting (wrapping text, bold headers).
