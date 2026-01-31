# Freelance Research Scout 🔍

An agentic, multi-tenant research operating system designed for elite freelance researchers. Built with Streamlit, Supabase, and Gemini 2.0 Flash.

## ✨ Features
- **Hybrid Scout**: Internal memory + Academic Graph (Semantic Scholar) + Grey Literature (DDG).
- **Auto-Pilot**: Autonomous keyword refinement loop.
- **Deep Ingestion**: PDF metadata extraction & Firecrawl web scraping with Pydantic validation.
- **Library Management**: Snowball Mining (recursive citations) & Citation previews.
- **Deliverables**: Word XML Bibliography, Excel Matrix, and Notion Sync.
- **Ghostwriter**: Advanced RAG synthesis with mandatory inline citations.

## 🛠️ Prerequisites
- Python 3.11+
- Supabase Account (Postgres + SQL Editor)
- Google Gemini API Key
- Firecrawl API Key (Optional for deep scraping)
- Notion API Token (Optional for syncing)

## 🚀 Quick Start
1. **Clone & Install**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Setup Database**: Run `schema.sql` in your Supabase SQL Editor.
3. **Configure Secrets**: Copy `.streamlit/secrets_template.toml` to `.streamlit/secrets.toml` and fill in your keys.
4. **Run**:
   ```bash
   streamlit run freelance_scout.py
   ```

## ☁️ Deployment Guide (Streamlit Community Cloud)

1. **GitHub Repository**:
   - Create a new Private repository on GitHub.
   - Push all files **EXCEPT** `.streamlit/secrets.toml` (which is gitignored).
2. **Connect to Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io).
   - Click "New app" and select your repository and the `freelance_scout.py` file.
3. **Configure Secrets**:
   - In the Streamlit Cloud deployment settings, go to **Secrets**.
   - Paste the contents of your local `secrets.toml` into the secrets area.
4. **Deploy**: Click "Deploy" and your Research OS is live!

---
*Developed by Antigravity AI.*
