# Deployment Guide: Elite Research Scout ⚜️

This guide outlines the steps to deploy "The Factory" to Streamlit Cloud.

## 1. Prerequisites
*   **GitHub Repository:** Ensure your code is pushed to a private GitHub repository.
*   **Streamlit Cloud Account:** Sign up at [share.streamlit.io](https://share.streamlit.io/).
*   **Supabase Project:** A live Supabase project with the schema applied.
*   **API Keys:**
    *   Google Gemini API Key
    *   Supabase URL & Key
    *   Firecrawl API Key (Optional)
    *   Notion Integration Token (Optional)

## 2. Configuration (`secrets.toml`)
On Streamlit Cloud, you cannot use a local `.toml` file. You must enter these in the **"Secrets"** settings of your app dashboard.

```toml
[supabase]
url = "YOUR_SUPABASE_URL"
key = "YOUR_SUPABASE_ANON_KEY"

[google]
api_key = "YOUR_GEMINI_API_KEY"

[firecrawl]
api_key = "YOUR_FIRECRAWL_KEY"

[notion]
api_token = "YOUR_NOTION_INTEGRATION_TOKEN"
database_id = "YOUR_NOTION_DATABASE_ID"
```

## 3. Dependencies (`requirements.txt`)
Ensure your `requirements.txt` includes all necessary packages. The system has automatically generated this, but verify it contains:
*   `streamlit`
*   `supabase`
*   `google-generativeai`
*   `pandas`
*   `requests`
*   `pypdf`
*   `openpyxl`
*   `duckduckgo-search`
*   `pydantic`
*   `firecrawl-py`
*   `streamlit-agraph`
*   `streamlit-extras`

## 4. Deployment Steps
1.  Go to [Streamlit Cloud](https://share.streamlit.io/).
2.  Click **"New app"**.
3.  Select your GitHub repository, branch (`main`), and file (`freelance_scout.py`).
4.  Click **"Advanced Settings"** -> **"Secrets"** and paste the TOML configuration above.
5.  Click **"Deploy"**.

## 5. Troubleshooting
*   **401 Errors:** Check your Supabase URL/Key.
*   **Module Not Found:** Check `requirements.txt`.
*   **Graph Issues:** `streamlit-agraph` can sometimes struggle on cloud instances if memory is low. If it crashes, remove it from the requirements and the code.

---
**Status:** Ready for Launch.
