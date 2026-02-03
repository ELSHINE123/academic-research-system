# Phase 3 Context: Citation & Relationship Mapping

## Phase Goal
Transform the static "Research Archive" into a dynamic, interconnected knowledge graph. Move beyond simple lists to visualization of influence and recursive discovery.

## 1. Citation Matrix (The "Library" Upgrade)
**"Interactive Knowledge Table"**

*   **View:** Upgrade the `st.data_editor` to a "Citation Matrix" view.
*   **Columns:**
    *   **Title/Author/Year**: Standard metadata.
    *   **Status**: `Unread`, `Reading`, `Synthesized`.
    *   **Impact Score**: A calculated metric (Citation Count / Year Age).
    *   **Tags**: Multi-select tags (e.g., `Methodology`, `Theory`).
*   **Actions:** "Quick Synthesis" button (triggers a mini-summary in the side panel).

## 2. Recursive Snowball Mining (The "Graph Digger")
**"Automated Bibliography Expansion"**

*   **Current State:** Basic one-level lookup.
*   **Upgrade:**
    *   **Depth Control:** User selects recursion depth (1-2 levels).
    *   **Filter:** "Only include papers with > N citations" or "Published after YYYY".
    *   **Visual Feedback:** Show a progress bar for mining operations.
    *   **Deduplication:** Strict check against existing `project_id` records before insertion.

## 3. Relationship Visualization (The "Network")
**"Visualizing the Conversation"**

*   **Tool:** `streamlit-agraph` or `graphviz`.
*   **Nodes:** Papers (Size = Citation Count).
*   **Edges:** Shared Authors or Direct Citations (if available).
*   **Interactive:** Clicking a node opens the paper details in the Synthesis Workspace.

## Technical Implementation (Planner Notes)
*   **Database:**
    *   `papers` table: Add `citation_count`, `impact_score`, `tags` (ARRAY), `reading_status`.
*   **API:**
    *   Semantic Scholar Graph API: Use `citations` endpoint heavily.
*   **UI:**
    *   Add a "Graph View" tab to the Intelligence Feed.
