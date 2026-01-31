import streamlit as st
import pandas as pd
import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from supabase import create_client, Client
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Optional
from pypdf import PdfReader
from firecrawl import FirecrawlApp
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.add_vertical_space import add_vertical_space
import logfire

# --- OBSERVABILITY ---
try:
    logfire_token = st.secrets.get("logfire", {}).get("token")
    if logfire_token:
        logfire.configure(token=logfire_token)
        logfire.instrument_requests()
except Exception:
    pass
from duckduckgo_search import DDGS
import openpyxl
from io import BytesIO

# --- SCHEMAS ---
class PaperAnalysis(BaseModel):
    relevant: bool = Field(description="Is this paper relevant to the query?")
    summary: str = Field(description="One-sentence summary of the paper.")
    method: str = Field(description="Core methodology used in the paper.")

class SynthesisResponse(BaseModel):
    answer: str = Field(description="The academic synthesis of the library.")
    sources: List[str] = Field(description="List of keys used (Author, Year).")

class Metadata(BaseModel):
    title: str = Field(description="Title of the paper.")
    authors: List[str] = Field(description="List of author names.")
    year: int = Field(description="Publication year.")
    abstract: str = Field(description="Brief abstract.")

# --- HELPER: WORD BIBLIOGRAPHY XML ---
def generate_word_xml_bib(papers):
    ns = "{http://schemas.microsoft.com/office/word/2004/10/bibliography}"
    root = ET.Element(f"{ns}Sources", {
        "SelectedStyle": "\\APA.XSL",
        "xmlns:b": "http://schemas.microsoft.com/office/word/2004/10/bibliography",
        "xmlns": "http://schemas.microsoft.com/office/word/2004/10/bibliography"
    })
    
    for p in papers:
        source = ET.SubElement(root, f"{ns}Source")
        ET.SubElement(source, f"{ns}Tag").text = f"REF{p['id'][:4]}"
        ET.SubElement(source, f"{ns}SourceType").text = "JournalArticle"
        
        author_list = ET.SubElement(source, f"{ns}Author")
        authors = ET.SubElement(author_list, f"{ns}Author")
        name_list = ET.SubElement(authors, f"{ns}NameList")
        for a_name in p['authors']:
            person = ET.SubElement(name_list, f"{ns}Person")
            ET.SubElement(person, f"{ns}Last").text = a_name.split()[-1] if ' ' in a_name else a_name
            ET.SubElement(person, f"{ns}First").text = a_name.split()[0] if ' ' in a_name else ""
            
        ET.SubElement(source, f"{ns}Title").text = p['title']
        ET.SubElement(source, f"{ns}Year").text = str(p['year'])
        if p.get('url'):
            ET.SubElement(source, f"{ns}URL").text = p['url']

    return ET.tostring(root, encoding='utf-8', method='xml')

# --- INITIALIZATION & CONFIG ---
st.set_page_config(
    page_title="Freelance Research Scout",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Premium Aesthetic
st.markdown("""
<style>
    :root {
        --primary-color: #D4AF37; /* Brush Gold */
        --bg-color: #0E1117;
        --secondary-bg: #1A1C24;
    }
    .stApp {
        background-color: var(--bg-color);
        color: #E0E0E0;
    }
    .main-header {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 2.5rem;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        font-size: 1rem;
        color: #888;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: var(--primary-color) !important;
        color: black !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.4);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: var(--primary-color) !important;
        border-bottom-color: var(--primary-color) !important;
    }
    .res-card {
        background-color: var(--secondary-bg);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid var(--primary-color);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- CLIENTS & SERVICES ---
@st.cache_resource
def init_supabase():
    url: str = st.secrets["supabase"]["url"]
    key: str = st.secrets["supabase"]["key"]
    return create_client(url, key)

@st.cache_resource
def init_gemini():
    api_key = st.secrets["google"].get("api_key")
    if not api_key or api_key == "PASTE_YOUR_GEMINI_API_KEY_HERE":
        st.error("Gemini API Key missing in secrets.toml")
        st.stop()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

@st.cache_resource
def init_firecrawl():
    api_key = st.secrets["firecrawl"].get("api_key")
    if not api_key or api_key == "PASTE_YOUR_FIRECRAWL_API_KEY_HERE":
        return None
    return FirecrawlApp(api_key=api_key)

try:
    db = init_supabase()
    ai = init_gemini()
    firecrawl = init_firecrawl()
except Exception as e:
    st.error(f"Initialization Error: {e}")
    st.stop()

# --- AUTHENTICATION ---
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Login"

# Inject JWT for RLS enforcement
if st.session_state.user:
    try:
        db.postgrest.auth(st.session_state.user.access_token)
    except:
        pass

def auth_gate():
    """Handles Multi-User Sign In and Registration."""
    if not st.session_state.user:
        # Premium CSS for Login Page
        st.markdown("""
            <style>
            .stApp {
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            }
            .login-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 3rem;
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(20px);
                border-radius: 24px;
                border: 1px solid rgba(212, 175, 55, 0.2);
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                max-width: 500px;
                margin: 50px auto;
                animation: fadeIn 1s ease-out;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .login-title {
                color: #D4AF37;
                font-size: 2.5rem;
                font-weight: 800;
                margin-bottom: 0.5rem;
                text-align: center;
                letter-spacing: -1px;
            }
            .login-subtitle {
                color: #94a3b8;
                font-size: 0.9rem;
                margin-bottom: 2rem;
                text-align: center;
            }
            .stButton>button {
                width: 100%;
                background: linear-gradient(90deg, #D4AF37 0%, #B8860B 100%);
                color: #0f172a !important;
                border: none;
                font-weight: 700;
                padding: 0.75rem;
                border-radius: 12px;
                transition: all 0.3s ease;
            }
            .stButton>button:hover {
                transform: scale(1.02);
                box-shadow: 0 0 20px rgba(212, 175, 55, 0.4);
            }
            input {
                background: rgba(15, 23, 42, 0.6) !important;
                border: 1px solid rgba(212, 175, 55, 0.3) !important;
                color: white !important;
                border-radius: 12px !important;
            }
            .auth-toggle {
                cursor: pointer;
                color: #D4AF37;
                text-decoration: underline;
                font-weight: 600;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Logo handling
        try:
            st.image("assets/logo.png", width=100)
        except:
            st.markdown('<div style="font-size: 3rem; text-align: center;">⚜️</div>', unsafe_allow_html=True)

        st.markdown(f'<h1 class="login-title">{st.session_state.auth_mode}</h1>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">Secured Research Terminal v2.0</p>', unsafe_allow_html=True)
        
        email = st.text_input("Email", placeholder="researcher@agency.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        if st.session_state.auth_mode == "Login":
            if st.button("Unlock System"):
                try:
                    res = db.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    st.rerun()
                except Exception as e:
                    st.error(f"Login Failed: {str(e)}")
            
            st.markdown("---")
            st.markdown("New to the Agency?")
            if st.button("Create an Account"):
                st.session_state.auth_mode = "Register"
                st.rerun()
        
        else:
            full_name = st.text_input("Full Name", placeholder="Alexander Pierce")
            if st.button("Join the Agency"):
                try:
                    res = db.auth.sign_up({"email": email, "password": password})
                    if res.user:
                        # Initialize Profile
                        db.table("profiles").insert({
                            "id": res.user.id,
                            "full_name": full_name
                        }).execute()
                        st.success("Account Created! Please check your email for verification.")
                        st.session_state.auth_mode = "Login"
                        st.rerun()
                except Exception as e:
                    st.error(f"Registration Failed: {str(e)}")
            
            if st.button("Back to Login"):
                st.session_state.auth_mode = "Login"
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        return False
    return True

# --- AUTHENTICATION GATE ---
if not auth_gate():
    st.stop()

# --- SIDEBAR: MULTI-TENANT CONTROL ---
with st.sidebar:
    try:
        st.image("assets/logo.png", width=150)
    except:
        pass
    
    # User Profile & Logout
    st.markdown("### 👤 Researcher Profile")
    st.write(f"Logged in as: **{st.session_state.user.email}**")
    if st.button("Logout", use_container_width=True):
        db.auth.sign_out()
        st.session_state.user = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Project Control")
    
    try:
        # RLS handles user isolation automatically
        projects_res = db.table("projects").select("*").order("created_at", desc=True).execute()
        projects = projects_res.data
    except:
        projects = []
    
    if projects:
        project_names = [p["name"] for p in projects]
        selected_project_name = st.selectbox("Active Project", project_names)
        active_project = next(p for p in projects if p["name"] == selected_project_name)
        st.session_state.project_id = active_project["id"]
        st.info(f"📁 Managing: **{active_project['client_name']}**")
    else:
        st.warning("No projects found.")
        st.session_state.project_id = None

    add_vertical_space(1)
    st.markdown("---")
    st.markdown("### New Client Onboarding")
    new_client = st.text_input("Client Name - Topic", help="Syntax: Client Name - Project Title")
    if st.button("Create Project", use_container_width=True) and new_client:
        parts = new_client.split(" - ")
        c_name = parts[0]
        p_name = parts[1] if len(parts) > 1 else parts[0]
        # owner_id will be set by DB default auth.uid()
        db.table("projects").insert({"name": p_name, "client_name": c_name}).execute()
        st.success(f"Project '{p_name}' created!")
        st.rerun()

# --- MAIN APP UI ---
st.markdown(f"<div class='main-header'>Freelance Research Scout</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-header'>Agentic Research OS | Project: {selected_project_name if 'project_id' in st.session_state and st.session_state.project_id else 'None'}</div>", unsafe_allow_html=True)

tabs = st.tabs(["🔍 Hybrid Scout", "📥 Ingest Station", "📚 Library", "🧾 Deliverables", "✍️ Ghostwriter"])

# --- TAB 1: HYBRID SCOUT ---
with tabs[0]:
    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_input("Search Query", placeholder="e.g. 'Impact of LLMs on Software Engineering Productivity'")
    with col2:
        include_grey = st.checkbox("Include Grey Literature (Web PDF Search)")
        auto_pilot = st.checkbox("Enable Auto-Pilot Loop")

    if st.button("Scout Knowledge Frontier", use_container_width=True):
        if not st.session_state.project_id:
            st.error("Select a project first.")
        else:
            # 1. Zone A: Internal Memory
            st.markdown("### 🧠 Zone A: Internal Memory")
            internal_res = db.table("papers").select("*").ilike("title", f"%{query}%").execute()
            if internal_res.data:
                for p in internal_res.data:
                    with st.container():
                        cols = st.columns([4, 1])
                        cols[0].write(f"**{p['title']}** ({p['year']}) - *Project: {p['project_id'][:6]}*")
                        if cols[1].button("Clone to Active", key=f"clone_{p['id']}"):
                            db.table("papers").insert({
                                "project_id": st.session_state.project_id,
                                "title": p['title'], "authors": p['authors'],
                                "year": p['year'], "abstract": p['abstract'],
                                "url": p['url'], "source_type": "internal-memory"
                            }).execute()
                            st.toast("Cloned to active project!")
            else:
                st.info("No matches in previous projects.")

            # 2. Zone B: External Frontier
            st.markdown("---")
            st.markdown("### 🌐 Zone B: External Frontier")
            
            def perform_scout(search_term):
                ss_results = []
                with st.spinner(f"Scouting External Sources for '{search_term}'..."):
                    # Academic
                    ss_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={search_term}&limit=10&fields=title,authors,year,abstract,url,citationCount"
                    resp = requests.get(ss_url)
                    if resp.status_code == 200:
                        ss_results = resp.json().get("data", [])
                    
                    # Grey Lit (DDG PDF Search)
                    if include_grey:
                        with DDGS() as ddgs:
                            ddg_results = ddgs.text(f"{search_term} filetype:pdf", max_results=5)
                            for dr in ddg_results:
                                ss_results.append({
                                    "title": dr['title'], "url": dr['href'],
                                    "abstract": dr['body'], "authors": [{"name": "Web Source"}],
                                    "year": datetime.now().year, "source_type": "grey"
                                })

                    # AI Relevancy Loop
                    final_papers = []
                    for p in ss_results:
                        prompt = f"Target: '{search_term}'. Analysis abstract/snip: {p.get('abstract', '') or p.get('body', '')}. Return JSON matching schema."
                        try:
                            # Using JSON Mode if possible, or parsing string
                            ai_resp = ai.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                            analysis = PaperAnalysis.model_validate_json(ai_resp.text)
                            if analysis.relevant:
                                p.update(analysis.model_dump())
                                final_papers.append(p)
                        except Exception as e:
                            # Fallback if JSON mode fails
                            continue
                    return final_papers

            results = perform_scout(query)
            
            # --- AGENTIC AUTO-PILOT LOOP ---
            if auto_pilot and len(results) < 3:
                st.warning(f"Low relevance found ({len(results)} papers). Triggering Auto-Pilot Keyword Refinement...")
                refine_prompt = f"The query '{query}' yielded poor research results. Suggest 3 highly academic and specific boolean search strings for this topic. Return as a comma separated list."
                ai_refine = ai.generate_content(refine_prompt)
                new_keywords = ai_refine.text.split(",")[0].strip()
                st.info(f"Refining search to: **{new_keywords}**")
                results += perform_scout(new_keywords)

            if results:
                for p in results:
                    with st.container():
                        st.markdown(f"<div class='res-card'><h4>{p['title']}</h4><p>{p.get('summary', 'No summary available')}</p></div>", unsafe_allow_html=True)
                        if st.button("Save", key=f"ext_{p['title']}"):
                            authors = [a.get('name', 'Unknown') for a in p['authors']] if isinstance(p['authors'], list) else ["Web Source"]
                            db.table("papers").insert({
                                "project_id": st.session_state.project_id,
                                "title": p['title'], "authors": authors,
                                "year": p.get('year'), "abstract": p.get('abstract'),
                                "url": p.get('url'), "summary": p.get('summary'),
                                "methodology": p.get('methodology'),
                                "source_type": p.get('source_type', 'external')
                            }).execute()
                            st.toast("Saved!")

# --- TAB 2: INGEST STATION ---
with tabs[1]:
    ingest_mode = st.radio("Ingest Type", ["PDF Deep Parse", "Web/Firecrawl Scrape"])
    
    if ingest_mode == "PDF Deep Parse":
        uploaded_file = st.file_uploader("Upload PDF", type="pdf")
        if uploaded_file and st.session_state.project_id:
            reader = PdfReader(uploaded_file)
            text = "".join([p.extract_text() for p in reader.pages[:5]])
            prompt = f"Extract metadata. Return JSON matching schema. Text: {text[:4000]}"
            ai_resp = ai.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            meta = Metadata.model_validate_json(ai_resp.text)
            st.json(meta.model_dump())
            if st.button("Confirm Ingest"):
                db.table("papers").insert({
                    "project_id": st.session_state.project_id, **meta.model_dump(), "source_type": "manual-pdf"
                }).execute()
    
    elif ingest_mode == "Web/Firecrawl Scrape" and firecrawl:
        web_url = st.text_input("Enter Web URL for Deep Scraping")
        if st.button("Crawl & Analyze"):
            with st.spinner("Firecrawl in progress..."):
                scrape_res = firecrawl.scrape_url(web_url, params={'formats': ['markdown']})
                markdown = scrape_res.get('markdown', '')
                prompt = f"Analyze this webpage content. Extract metadata and summarize. Return JSON: {{title: str, summary: str, methodology: str}}. Content: {markdown[:5000]}"
                web_analysis = json.loads(ai.generate_content(prompt).text.replace("```json", "").replace("```", "").strip())
                st.write(web_analysis)
                if st.button("Save Web Resource"):
                    db.table("papers").insert({
                        "project_id": st.session_state.project_id,
                        "title": web_analysis['title'], "summary": web_analysis['summary'],
                        "abstract": markdown[:2000], "url": web_url, "source_type": "firecrawl-scrape"
                    }).execute()

# --- TAB 3: LIBRARY ---
with tabs[2]:
    if st.session_state.project_id:
        papers = db.table("papers").select("*").eq("project_id", st.session_state.project_id).execute().data
        if papers:
            df = pd.DataFrame(papers)
            style = st.radio("Citation Style", ["APA", "MLA", "Harvard"], horizontal=True)
            def fmt(r):
                a = r['authors'][0] if r['authors'] else "Anon"
                return f"{a} ({r['year']}). {r['title']}." if style == "APA" else f"{a}. '{r['title']}'."
            df['Citation'] = df.apply(fmt, axis=1)
            st.data_editor(df[['title', 'Citation', 'year', 'source_type']], use_container_width=True)
            
            # --- SNOWBALL MINING (RECURSIVE) ---
            st.markdown("---")
            target = st.selectbox("Select for Snowball Mine (Fetch Citations)", df['title'].tolist())
            if st.button("⛏️ Mine Recursive Citations"):
                with st.spinner("Mining Research Graph..."):
                    # 1. Search for paper to get SS ID
                    ss_search = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/search?query={target}&limit=1&fields=paperId").json()
                    if ss_search.get("data"):
                        pid = ss_search["data"][0]["paperId"]
                        # 2. Get References
                        ref_url = f"https://api.semanticscholar.org/graph/v1/paper/{pid}/references?limit=5&fields=title,authors,year,abstract,url"
                        refs = requests.get(ref_url).json().get("data", [])
                        for r_item in refs:
                            r = r_item.get("citedPaper")
                            if r and r.get("title"):
                                db.table("papers").insert({
                                    "project_id": st.session_state.project_id,
                                    "title": r['title'], "authors": [a.get('name', 'Unknown') for a in r.get('authors', [])],
                                    "year": r.get('year'), "abstract": r.get('abstract'), "url": r.get('url'),
                                    "source_type": "snowball-mining"
                                }).execute()
                        st.success(f"Mined {len(refs)} new relevant references. Added to library.")
                    else:
                        st.error("Could not find paper in Semantic Scholar Graph.")

# --- TAB 4: DELIVERABLES ---
with tabs[3]:
    st.markdown("### Export Matrix & Bibliography")
    papers_data = db.table("papers").select("*").eq("project_id", st.session_state.project_id).execute().data
    if papers_data:
        col1, col2, col3 = st.columns(3)
        with col1:
            xml_data = generate_word_xml_bib(papers_data)
            st.download_button("Download Word Bib (XML)", xml_data, "bibliography.xml", "text/xml")
        with col2:
            buffer = BytesIO()
            pd.DataFrame(papers_data).to_excel(buffer, index=False)
            st.download_button("Download Excel Matrix", buffer.getvalue(), "matrix.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col3:
            if st.button("🚀 Sync to Notion"):
                notion_token = st.secrets["notion"].get("api_token")
                database_id = st.secrets["notion"].get("database_id")
                if notion_token and database_id:
                    with st.spinner("Syncing to Notion..."):
                        headers = {
                            "Authorization": f"Bearer {notion_token}",
                            "Content-Type": "application/json",
                            "Notion-Version": "2022-06-28"
                        }
                        success_count = 0
                        for p in papers_data:
                            data = {
                                "parent": {"database_id": database_id},
                                "properties": {
                                    "Title": {"title": [{"text": {"content": p['title']}}]},
                                    "Year": {"number": p['year']} if p['year'] else None,
                                    "Authors": {"rich_text": [{"text": {"content": ", ".join(p['authors'])}}]},
                                    "URL": {"url": p['url']} if p['url'] else None
                                }
                            }
                            # Filter None properties
                            data["properties"] = {k: v for k, v in data["properties"].items() if v is not None}
                            res = requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
                            if res.status_code == 200: success_count += 1
                        st.success(f"Synced {success_count} papers to Notion!")
                else:
                    st.warning("Notion API Token or Database ID missing in secrets.toml")

# --- TAB 5: GHOSTWRITER ---
with tabs[4]:
    st.markdown("### RAG Research Synthesis")
    if st.session_state.project_id:
        papers_rag = db.table("papers").select("*").eq("project_id", st.session_state.project_id).execute().data
        kb = "\n".join([f"KEY: ({p['authors'][0] if p['authors'] else 'n.a'}, {p['year']}) | CONTENT: {p.get('summary') or p.get('abstract')}" for p in papers_rag])
        
        if prompt := st.chat_input("Synthesize a claim..."):
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                sys = f"Expert Ghostwriter. Rules: 1. Use ONLY context. 2. Inline citations (Author, Year) are MANDATORY. 3. No hallucinating. Return JSON matching schema.\nCONTEXT:\n{kb}"
                ai_resp = ai.generate_content(f"{sys}\nPROMPT: {prompt}", generation_config={"response_mime_type": "application/json"})
                try:
                    res = SynthesisResponse.model_validate_json(ai_resp.text)
                    st.markdown(res.answer)
                    st.caption(f"Sources used: {', '.join(res.sources)}")
                except:
                    st.markdown(ai_resp.text)
