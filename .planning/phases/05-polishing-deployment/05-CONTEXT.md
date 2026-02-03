# Phase 5 Context: Polishing & Deployment

## Phase Goal
Ensure the application is robust, error-tolerant, and ready for production deployment on Streamlit Cloud.

## 1. Error Handling & Resilience
**"Graceful Failure"**

*   **API Wrappers:** Wrap all external calls (Notion, Firecrawl, Gemini, Semantic Scholar) in `try-except` blocks.
*   **User Feedback:** Use `st.toast` for minor errors and `st.error` for blocking issues. Avoid app crashes (red screens).
*   **Validation:** Ensure inputs (URLs, PDFs) are validated before processing.

## 2. UI/UX Refinement
**"The Factory Polish"**

*   **Consistency:** Verify "The Factory" theme is applied to all new elements (Network Graph, Matrix).
*   **Loading States:** Ensure `st.spinner` or `st.status` is used for all long-running operations.

## 3. Deployment Artifacts
*   **`requirements.txt`:** Verify all dependencies are listed (`streamlit-agraph`, `openpyxl`, `firecrawl-py`).
*   **`DEPLOYMENT.md`:** A step-by-step guide for deploying to Streamlit Cloud, including `secrets.toml` configuration.

## Technical Implementation (Planner Notes)
*   **Notion Sync:** Add progress bar and individual item error handling (don't fail batch on one error).
*   **Firecrawl:** Handle timeouts or 4xx/5xx errors gracefully.
*   **Gemini:** Handle quota limits (429) with a friendly message.
