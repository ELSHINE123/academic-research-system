# Phase 2 Context: The Research Cockpit & Intelligence Engine

## Phase Goal
Total workflow transformation. Pivot from a segmented "tabbed" app to a unified "Research Cockpit" while integrating autonomous intelligence gathering and deep-document ingestion.

## 1. UX Paradigm: The Research Cockpit
**"Unified Visibility, Zero Context-Switching"**

*   **Split-Screen Layout (Workbench):**
    *   **Left Pane (Intelligence Feed):** A scrollable stream containing:
        *   **The Review Queue:** New arrivals from Auto-Pilot/Firecrawl (Actionable: Keep/Discard).
        *   **Search Results:** Live results from current Scout queries.
        *   **Active Library:** Recent/Pinned papers from the project database.
    *   **Right Pane (Synthesis Workspace):** The permanent editor and Synthesis Engine.
        *   Always visible.
        *   Supports "Drafting" while viewing papers on the left.
*   **Unified Command Bar:**
    *   One input field at the top of the Intelligence Feed.
    *   Detects intent: Keywords = Search; URL = Firecrawl; PDF = Ingest.
*   **Visual Style: "Clean Industrial":**
    *   High-legibility typography (Inter/SF Pro).
    *   Switch from "Decorative Factory" (Ivory/Gold) to a professional, dark-mode-ready, high-density dashboard.
    *   Use `st.columns` and `st.container` to maximize vertical space usage.

## 2. Auto-Pilot Refinement Logic
**"The Autonomous Analyst"**

*   **Trigger:** Activates when initial search yields **< 10 results**.
*   **Strategy:** **Broaden Scope**. Use synonyms and broader academic terms.
*   **Workflow:** **Proposal Mode**. The system pauses, shows the refined keywords (`[search_terms]`, `[filter_criteria]`, `[data_source]`), and waits for user "Execute" confirmation.
*   **Transparency:** Display a **"Logic Trace"** (e.g., "Refined 'X' to 'Y' (+12 results)") directly in the Intelligence Feed.

## 3. Grey Literature & Search
**"Multi-Source Grounding"**

*   **Logic:** Semantic search grounded in **Top N=5** results.
*   **Filters:** Prioritize `.gov`, `.edu`. Types: `report`, `article`, `patent`.
*   **Quality:** AI Credibility Check (Credibility=High). Deduplicate findings.
*   **Ordering:** Sort by Date if relevance is equal.
*   **Presentation:** Grey Lit must have a distinct visual badge/color in the Intelligence Feed to separate it from Peer-Reviewed sources.

## 4. Firecrawl & Full-Text Ingest
**"Deep Metadata & Content RAG"**

*   **Dual-Mode:** Manual (User pastes URL) and Autonomous (Agent visits search results).
*   **Scope:** Single Page (Strict).
*   **Fallbacks:** Save as "Web Capture" if metadata is missing.
*   **Intelligence Pipeline:** Firecrawl findings -> **Review Queue** -> (User Approve) -> Library.
*   **Storage:** Save **Full Markdown** in `content_body` for deep RAG queries.

## 5. PDF Engine: Optimized Chunking & Vision
**"Universal Document Reader"**

*   **Framework:** Implement full-document processing (abandon 5-page limit).
*   **Chunking:** Optimized Semantic/Recursive chunking (~1024 tokens, 128 overlap).
*   **Embedding:** `text-embedding-004`.
*   **Vision:** Use Gemini Vision for **OCR** (scanned docs) and **Chart/Image interpretation**.
*   **Persistence:** Store text + vision descriptions in `content_body`.

## Technical Implementation (Planner Notes)
*   **Database Migrations:**
    *   `papers` table: Add `content_body` (TEXT), `status` (active/review), `source_type` (web/academic/grey/pdf), `credibility_score`.
*   **Layout Engine:** Use `st.container` and `st.empty` to create a "live" feed feel in the Intelligence Pane.
*   **Component Sync:** Ensure the Synthesis Engine (Right) can pull context directly from the currently "Selected" paper in the Intelligence Feed (Left).