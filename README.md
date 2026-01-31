# Elite Research Scout ⚜️

A premium, luxury-grade agentic research terminal designed for elite researchers. Built with Streamlit, Supabase, and Gemini 2.0 Flash.

## 💎 Elite Features
- **Luxury Interface**: Stunning glassmorphic design with custom gradients and premium typography.
- **Multi-User Security**: Individual researcher accounts with database-level Row Level Security (RLS).
- **Hybrid Scout**: Internal memory scan + Global Academic Graph (Semantic Scholar) + Grey Literature (Web PDF Search).
- **Auto-Pilot Loop**: Autonomous keyword refinement engine for deep intelligence gathering.
- **Digital Ingest**: PDF metadata extraction and Firecrawl deep-scraping with Pydantic validation.
- **Citation Matrix**: Interactive library with Snowball Mining (recursive citation discovery).
- **Export Lounge**: Word XML Bibliography, Excel Matrix, and Notion Workspace integration.
- **Synthesis Engine**: Advanced RAG synthesis with mandatory grounded inline citations.

## 🛠️ Prerequisites
- Python 3.11+
- [Supabase](https://supabase.com/) Account (Postgres + Auth)
- Google Gemini API Key
- Firecrawl API Key (Optional for deep scraping)
- Notion API Token (Optional for syncing)

## 🚀 Deployment & Setup

### 1. Database Configuration
1. Create a new Supabase project.
2. In the **SQL Editor**, run the contents of [schema.sql](schema.sql) to initialize tables.
3. Run [migration.sql](migration.sql) to enable multi-user RLS and profiles.
4. In **Authentication > Providers**, ensure Email is enabled.

### 2. Local Environment
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.streamlit/secrets_template.toml` to `.streamlit/secrets.toml` and add your keys.
4. Launch the terminal: `streamlit run freelance_scout.py`

### 3. Streamlit Community Cloud (Live)
1. Push your code to a private GitHub repository.
2. Connect the repo at [share.streamlit.io](https://share.streamlit.io).
3. **Critical**: Paste your `secrets.toml` content into the Streamlit Cloud **Advanced Settings > Secrets** section.
4. Your luxury research terminal is now live at your custom URL.

---
*Developed for the elite researcher. Built by Antigravity AI.*
