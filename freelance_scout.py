import streamlit as st
import pandas as pd
from supabase import create_client, Client
import google.generativeai as genai
import requests
from io import BytesIO
from pypdf import PdfReader
from datetime import datetime
import json
from pydantic import BaseModel, Field
from typing import List, Optional
from streamlit_extras.add_vertical_space import add_vertical_space
from duckduckgo_search import DDGS
from firecrawl import FirecrawlApp
import xml.etree.ElementTree as ET

# --- CONFIGURATION & MODELS ---
st.set_page_config(
    page_title="Elite Research Scout",
    page_icon="⚜️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Premium CSS: THE ATELIER
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
<style>
    /* Atelier Core */
    .stApp {
        background: #FAF9F6;
        background-image: 
            radial-gradient(at 0% 0%, rgba(197, 160, 33, 0.05) 0px, transparent 50%),
            url("https://www.transparenttextures.com/patterns/natural-paper.png");
        color: #121212;
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, .main-header {
        font-family: 'Playfair Display', serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        color: #121212 !important;
    }

    /* Editorial Header */
    .main-header {
        font-size: 5rem !important;
        line-height: 1.1 !important;
        margin-bottom: 0rem !important;
        text-align: center;
        border-bottom: 1px solid #121212;
        padding-bottom: 1rem;
        margin-top: 2rem;
    }
    .sub-header {
        color: #C5A021;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.5em;
        text-align: center;
        margin-top: 1rem;
        margin-bottom: 5rem;
        font-weight: 400;
    }

    /* The Curator's Panel (Sidebar) */
    [data-testid="stSidebar"] {
        background: #fdfcf9 !important;
        border-right: 1px solid rgba(18, 18, 18, 0.1);
        box-shadow: 20px 0 60px rgba(0,0,0,0.03);
    }
    [data-testid="stSidebar"] h1 {
        font-size: 1.2rem !important;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        border-bottom: 1px solid #121212;
        padding-bottom: 0.5rem;
    }
    
    /* Atelier Buttons */
    .stButton>button {
        background: transparent !important;
        color: #121212 !important;
        font-weight: 600 !important;
        border-radius: 0px !important;
        border: 1px solid #121212 !important;
        padding: 0.7rem 2rem !important;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
    }
    .stButton>button:hover {
        background: #121212 !important;
        color: #FAF9F6 !important;
        padding-left: 2.5rem !important;
    }

    /* Atelier Cards */
    .atelier-card {
        background: #ffffff;
        border: 1px solid rgba(18, 18, 18, 0.08);
        padding: 3rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.02);
        position: relative;
        animation: fadeIn 0.8s ease-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .atelier-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0; width: 4px; height: 100%;
        background: #C5A021;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    .atelier-card:hover::before {
        opacity: 1;
    }

    /* Underline Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        padding: 0;
        border-bottom: 1px solid rgba(18, 18, 18, 0.1);
        display: flex;
        justify-content: center;
        gap: 30px;
        margin-bottom: 5rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        padding: 15px 5px !important;
        font-weight: 400 !important;
        font-size: 1rem !important;
        border: none !important;
        color: #94a3b8 !important;
        font-family: 'Playfair Display', serif !important;
        text-transform: capitalize;
    }
    .stTabs [aria-selected="true"] {
        color: #121212 !important;
        border-bottom: 2px solid #C5A021 !important;
    }

    /* Inputs */
    .stTextInput input {
        background: transparent !important;
        border: none !important;
        border-bottom: 1px solid rgba(18, 18, 18, 0.2) !important;
        border-radius: 0px !important;
        color: #121212 !important;
        font-size: 1.2rem !important;
        padding: 10px 0 !important;
    }
    .stTextInput input:focus {
        border-bottom: 1px solid #C5A021 !important;
        box-shadow: none !important;
    }

    /* Metrics & Stats */
    [data-testid="stMetricValue"] {
        color: #121212 !important;
        font-family: 'Playfair Display', serif !important;
        font-weight: 700 !important;
        font-size: 3rem !important;
    }

    /* Sector Badge */
    .sector-badge {
        font-family: 'Inter', sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        font-size: 0.75rem;
        color: #C5A021;
        text-align: center;
        margin-bottom: 3rem;
    }
</style>
""", unsafe_allow_html=True)

class PaperAnalysis(BaseModel):
    relevant: bool = Field(description="Is this paper highly relevant to the research query?")
    summary: str = Field(description="2-sentence academic summary focusing on findings.")
    methodology: str = Field(description="Primary research methodology used (e.g. Qualitative, Meta-analysis, Empirical).")

class Metadata(BaseModel):
    title: str = Field(description="Full academic title of the paper.")
    authors: List[str] = Field(description="List of all contributing authors.")
    year: Optional[int] = Field(description="Year of publication.")
    abstract: str = Field(description="Concise abstract or summary.")

class SynthesisResponse(BaseModel):
    answer: str
    citations: List[str]

@st.cache_resource
def init_supabase():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

@st.cache_resource
def init_gemini():
    genai.configure(api_key=st.secrets["google"]["api_key"])
    return genai.GenerativeModel('gemini-2.0-flash')

@st.cache_resource
def init_firecrawl():
    key = st.secrets["firecrawl"].get("api_key")
    return FirecrawlApp(api_key=key) if key else None

try:
    db = init_supabase()
    ai = init_gemini()
    firecrawl = init_firecrawl()
except Exception as e:
    st.error(f"Initialization Failed: {e}")
    st.stop()

def generate_word_xml_bib(papers):
    root = ET.Element("b:Sources", {
        "SelectedStyle": "\\APA.XSL",
        "xmlns:b": "http://schemas.openxmlformats.org/officeDocument/2006/bibliography",
        "xmlns": "http://schemas.openxmlformats.org/officeDocument/2006/bibliography"
    })
    for p in papers:
        source = ET.SubElement(root, "b:Source")
        ET.SubElement(source, "b:Tag").text = p['title'][:10] + str(p['year'])
        ET.SubElement(source, "b:SourceType").text = "JournalArticle"
        author_list = ET.SubElement(ET.SubElement(source, "b:Author"), "b:Author")
        names = ET.SubElement(author_list, "b:NameList")
        for a in p['authors']:
            person = ET.SubElement(names, "b:Person")
            ET.SubElement(person, "b:Last").text = a
        ET.SubElement(source, "b:Title").text = p['title']
        ET.SubElement(source, "b:Year").text = str(p['year'])
    return ET.tostring(root, encoding='utf-8')

# --- AUTHENTICATION ---
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Login" # Keep this line for initial state, though the new auth_gate might override it.

if st.session_state.user:
    try:
        db.postgrest.auth(st.session_state.user.access_token)
    except:
        pass

# Main Cinematic Header
st.markdown('<h1 class="main-header">THE ATELIER</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">ELITE RESEARCH SCOUT V2.0</p>', unsafe_allow_html=True)

# Auth Gate Logic with Obsidian Card
def auth_gate():
    if not st.session_state.user:
        st.markdown('<div class="atelier-card" style="max-width:550px; margin: 100px auto auto;">', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align:center; margin-bottom: 2rem;">Studio Access</h3>', unsafe_allow_html=True)
        
        auth_mode = st.radio("Access Level", ["Researcher Login", "New Studio Enrollment"], horizontal=True)
        
        email = st.text_input("Atelier Email")
        password = st.text_input("Credentials", type="password")
        
        if auth_mode == "Researcher Login":
            if st.button("Enter Studio"):
                try:
                    res = db.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    st.rerun()
                except Exception as e:
                    st.error(f"Access Denied: {str(e)}")
        else:
            if st.button("Enroll Researcher"):
                try:
                    res = db.auth.sign_up({"email": email, "password": password})
                    st.success("Enrollment requested. Please check your secure inbox.")
                except Exception as e:
                    st.error(f"Enrollment Error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        return False
    return True

if not auth_gate():
    st.stop()

# Sidebar: The Curator's Panel
with st.sidebar:
    st.markdown("<h1>The Curator's Panel</h1>", unsafe_allow_html=True)
    
    with st.expander("👤 ATELIER PROFILE", expanded=False):
        st.info(f"Identity: {st.session_state.user.email}")
        if st.button("Exit Studio"):
            db.auth.sign_out() # Changed supabase to db
            st.session_state.user = None
            st.rerun()

    st.markdown("---")
    # Project Selection / Allocation
    res = db.table("projects").select("*").eq("owner_id", st.session_state.user.id).execute()
    projects = res.data
    p_names = [p["name"] for p in projects]
    
    st.markdown("### Active Sectors")
    # Determine active_project and project_id based on selection
    if projects:
        sel = st.selectbox("Select Project Sector", p_names, key="sidebar_project_select")
        active_project = next(p for p in projects if p['name'] == sel)
        st.session_state.project_id = active_project['id']
    else:
        st.session_state.project_id = None
        st.info("No sectors allocated.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    with st.popover("➕ NEW ALLOCATION", use_container_width=True):
        new_p = st.text_input("New Sector Designation")
        if st.button("INITIATE ALLOCATION") and new_p:
            db.table("projects").insert({
                "name": new_p, 
                "client_name": "Agency",
                "owner_id": st.session_state.user.id
            }).execute()
            st.rerun()

    st.markdown("---")
    st.markdown("<p style='font-size: 0.6rem; color: #121212; text-align: center; opacity: 0.5;'>THE ATELIER v2.0.0<br>© 2026 ANTIGRAVITY AI</p>", unsafe_allow_html=True)

# --- MAIN UI ---
if st.session_state.project_id:
    st.markdown(f'<p class="sector-badge">Active Sector: {active_project["name"]}</p>', unsafe_allow_html=True)
    
    tabs = st.tabs([
        "🔍 Current Intelligence", 
        "📥 Resource Acquisitions", 
        "📚 The Research Archive", 
        "🧾 Intelligence Dossier", 
        "✍️ Manuscripts & Drafts"
    ])
    
    # 🔍 CURRENT INTELLIGENCE (SCOUT)
    with tabs[0]:
        st.markdown('<div class="atelier-card"><h3>Global Intelligence Scout</h3><p>Query Global Graphs and Web Frontiers.</p></div>', unsafe_allow_html=True)
        q = st.text_input("Intelligence Objective")
        col1, col2 = st.columns(2)
        grey = col1.toggle("Grey Literature Search")
        pilot = col2.toggle("Auto-Pilot Loop")
        
        if st.button("🚀 Execute Search", use_container_width=True):
            with st.status("Executing Intelligence Loop...") as status:
                st.markdown("#### 🧠 Internal Memory Scan")
                loc = db.table("papers").select("*").ilike("title", f"%{q}%").execute().data or []
                for p in loc:
                    st.write(f"💼 Found in Archives: **{p['title']}**")
                
                def perform_search(term):
                    # Semantic Scholar
                    ss = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/search?query={term}&limit=10&fields=title,authors,year,abstract,url").json().get("data", [])
                    # Grey Lit
                    if grey:
                        with DDGS() as ddgs:
                            for dr in ddgs.text(f"{term} filetype:pdf", max_results=5):
                                ss.append({"title": dr['title'], "url": dr['href'], "abstract": dr['body'], "authors": [{"name": "Web Source"}], "year": datetime.now().year, "source_type": "grey"})
                    return ss

                results = perform_search(q)
                if pilot and len(results) < 3:
                    st.info("Low results. Engaging Auto-Pilot Keyword Refinement...")
                    refine = ai.generate_content(f"Suggest 3 better academic search strings for '{q}'. Return as comma list.").text
                    results += perform_search(refine.split(',')[0])

                st.markdown("#### 🌐 Global Intelligence")
                for p in results:
                    with st.container():
                        st.markdown(f"<div class='atelier-card' style='padding:1.5rem; margin-bottom: 0.5rem;'><b>{p['title']}</b> ({p.get('year','n.a')})</div>", unsafe_allow_html=True)
                        if st.button("Archive Discovery", key=f"s_{p['title']}"):
                            db.table("papers").insert({
                                "project_id": st.session_state.project_id,
                                "title": p['title'], "authors": [a.get('name','Anon') for a in p.get('authors',[])],
                                "year": p.get('year'), "abstract": p.get('abstract'), "url": p.get('url'), "source_type": "scout"
                            }).execute()
                            st.toast("Saved!")
                status.update(label="Loop Complete", state="complete")

    # 📥 RESOURCE ACQUISITIONS (INGEST)
    with tabs[1]:
        st.markdown('<div class="atelier-card"><h3>Resource Acquisition Station</h3><p>Secure PDFs or ingest URLs with refined extraction.</p></div>', unsafe_allow_html=True)
        mode = st.radio("Channel", ["PDF", "URL"], horizontal=True)
        if mode == "PDF":
            up = st.file_uploader("Source PDF", type="pdf")
            if up:
                with st.spinner("Extracting..."):
                    tx = "".join([p.extract_text() for p in PdfReader(up).pages[:5]])
                    meta = Metadata.model_validate_json(ai.generate_content(f"Extract JSON from: {tx[:4000]}", generation_config={"response_mime_type": "application/json"}).text)
                    st.json(meta.model_dump())
                    if st.button("Confirm Archival"):
                        db.table("papers").insert({"project_id": st.session_state.project_id, **meta.model_dump(), "source_type": "pdf"}).execute()
                        st.success("Archived!")
        elif mode == "URL" and firecrawl:
            u = st.text_input("Source URL")
            if st.button("Scrape Sector"):
                with st.spinner("Firecrawl Engine Active..."):
                    sc = firecrawl.scrape_url(u, params={'formats': ['markdown']})
                    md = sc.get('markdown','')
                    ai_res = json.loads(ai.generate_content(f"Summarize and Extract: {md[:5000]}").text.replace("```json","").replace("```","").strip())
                    db.table("papers").insert({
                        "project_id": st.session_state.project_id, "title": ai_res.get('title','Web Source'),
                        "abstract": md[:2000], "url": u, "source_type": "web"
                    }).execute()
                    st.success("Web Intelligence Captured!")

    # 📚 LIBRARY
    with tabs[2]:
        paps = db.table("papers").select("*").eq("project_id", st.session_state.project_id).execute().data or []
        if paps:
            df = pd.DataFrame(paps)
            st.data_editor(df[['title', 'authors', 'year', 'source_type']], use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### 💎 Advanced Snowball Mining")
            target = st.selectbox("Select Seed Paper for Citation Mining", df['title'].tolist())
            if st.button("⛏️ Execute Recursive Mining"):
                with st.spinner("Mining Research Graph..."):
                    ss_search = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/search?query={target}&limit=1&fields=paperId").json()
                    if ss_search.get("data"):
                        pid = ss_search["data"][0]["paperId"]
                        ref_url = f"https://api.semanticscholar.org/graph/v1/paper/{pid}/references?limit=10&fields=title,authors,year,abstract,url"
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
                        st.success(f"Mined {len(refs)} references! Library updated.")
                    else:
                        st.error("Paper not found in Graph.")

    # 🧾 INTELLIGENCE DOSSIER (EXPORT)
    with tabs[3]:
        st.markdown('<div class="atelier-card"><h3>Intelligence Dossier Export</h3><p>Prepare the final handover documents for the sector.</p></div>', unsafe_allow_html=True)
        p_exp = db.table("papers").select("*").eq("project_id", st.session_state.project_id).execute().data or []
        if p_exp:
            exp_col1, exp_col2, exp_col3 = st.columns(3)
            with exp_col1:
                st.download_button("Word Bibliography (XML)", generate_word_xml_bib(p_exp), "bib.xml", use_container_width=True)
            with exp_col2:
                buf = BytesIO()
                pd.DataFrame(p_exp).to_excel(buf, index=False)
                st.download_button("Excel Research Matrix", buf.getvalue(), "matrix.xlsx", use_container_width=True)
            with exp_col3:
                if st.button("🚀 Sync to Notion", use_container_width=True):
                    token = st.secrets["notion"].get("api_token")
                    db_id = st.secrets["notion"].get("database_id")
                    if token and db_id:
                        with st.status("Syncing to Notion Workspace...") as status:
                            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
                            for p in p_exp:
                                data = {"parent": {"database_id": db_id}, "properties": {"Title": {"title": [{"text": {"content": p['title']}}]}, "Year": {"number": p['year']} if p['year'] else None, "Authors": {"rich_text": [{"text": {"content": ", ".join(p['authors'])}}]}, "URL": {"url": p['url']} if p['url'] else None}}
                                data["properties"] = {k: v for k, v in data["properties"].items() if v is not None}
                                requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)
                            status.update(label="Notion Sync Successful!", state="complete")
                    else: st.warning("Notion credentials missing in secrets.")

    # ✍️ MANUSCRIPTS & DRAFTS (SYNTHESIS)
    with tabs[4]:
        st.markdown('<div class="atelier-card"><h3>Editorial Synthesis Engine</h3><p>Grounded strictly in the curated project archives.</p></div>', unsafe_allow_html=True)
        papers_rag = db.table("papers").select("*").eq("project_id", st.session_state.project_id).execute().data or []
        kb = "\n".join([f"KEY: ({p['authors'][0] if p['authors'] else 'n.a'}, {p['year']}) | CONTENT: {p.get('abstract','')}" for p in papers_rag])
        if pr := st.chat_input("Synthesize intelligence..."):
            with st.chat_message("user"): st.write(pr)
            with st.chat_message("assistant"):
                sys_p = f"Professional Researcher. Use ONLY Context: {kb}"
                ai_r = ai.generate_content(f"{sys_p}\nPROMPT: {pr}")
                st.markdown(ai_r.text)

else:
    st.info("Unlock a Research Sector via Sidebar to Activate Terminal.")
