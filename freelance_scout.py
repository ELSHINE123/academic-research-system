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

# Custom Premium CSS for Luxury Analytics Terminal
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;700&display=swap" rel="stylesheet">
<style>
    /* Global Reset & Typography */
    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #0f172a);
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, .main-header {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
    }

    /* Main Header Styling */
    .main-header {
        background: linear-gradient(90deg, #D4AF37 0%, #F97316 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem !important;
        margin-bottom: 0rem !important;
        text-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .sub-header {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-top: -10px;
        margin-bottom: 2.5rem;
        font-weight: 300;
        letter-spacing: 0.05em;
    }

    /* Sidebar Styling - Elite Dark */
    [data-testid="stSidebar"] {
        background-color: #0c111d !important;
        border-right: 1px solid rgba(212, 175, 55, 0.15);
        box-shadow: 5px 0 30px rgba(0,0,0,0.5);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #D4AF37 0%, #B8860B 100%) !important;
        color: #0f172a !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 0.6rem 1.2rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(212,175,55,0.6) !important;
        transform: translateY(-2px);
    }

    /* Glassmorphic Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.03);
        padding: 5px;
        border-radius: 16px;
        backdrop-filter: blur(10px);
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease;
        color: #94a3b8 !important;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(212, 175, 55, 0.15) !important;
        color: #D4AF37 !important;
    }

    /* Premium Component Cards */
    .res-card {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-left: 4px solid #D4AF37;
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    .res-card:hover {
        background: rgba(255, 255, 255, 0.04);
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        border-left-width: 8px;
    }

    /* Form Elements */
    input, textarea, select {
        border-radius: 12px !important;
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
    st.session_state.auth_mode = "Login"

if st.session_state.user:
    try:
        db.postgrest.auth(st.session_state.user.access_token)
    except:
        pass

def auth_gate():
    if not st.session_state.user:
        st.markdown('<div class="res-card" style="max-width:500px; margin: 100px auto auto;">', unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align:center; color:#D4AF37;'>{st.session_state.auth_mode}</h1>", unsafe_allow_html=True)
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.session_state.auth_mode == "Login":
            if st.button("Unlock Terminal", use_container_width=True):
                try:
                    res = db.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    st.rerun()
                except Exception as e: st.error(e)
            if st.button("Request Credentials"):
                st.session_state.auth_mode = "Register"
                st.rerun()
        else:
            name = st.text_input("Full Name")
            if st.button("Join Archive", use_container_width=True):
                try:
                    res = db.auth.sign_up({"email": email, "password": password})
                    if res.user:
                        db.table("profiles").insert({"id": res.user.id, "full_name": name}).execute()
                        st.success("Signed Up! Check email.")
                        st.session_state.auth_mode = "Login"
                        st.rerun()
                except Exception as e: st.error(e)
            if st.button("Back to Security Desk"):
                st.session_state.auth_mode = "Login"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return False
    return True

if not auth_gate():
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#D4AF37;'>⚜️ Control</h2>", unsafe_allow_html=True)
    st.write(f"Logged in: {st.session_state.user.email}")
    if st.button("Logout", use_container_width=True):
        db.auth.sign_out()
        st.session_state.user = None
        st.rerun()
    st.markdown("---")
    
    projects = db.table("projects").select("*").order("created_at", desc=True).execute().data or []
    if projects:
        sel = st.selectbox("Active Sector", [p['name'] for p in projects])
        active_project = next(p for p in projects if p['name'] == sel)
        st.session_state.project_id = active_project['id']
    else:
        st.session_state.project_id = None
        st.warning("Create a project to start.")
    
    st.markdown("---")
    new_p = st.text_input("New Research Sector")
    if st.button("Allocate Sector") and new_p:
        db.table("projects").insert({"name": new_p, "client_name": "Agency"}).execute()
        st.rerun()

# --- MAIN UI ---
st.markdown('<h1 class="main-header">Elite Research Scout</h1>', unsafe_allow_html=True)
if st.session_state.project_id:
    st.markdown(f'<p class="sub-header">Active Sector: {active_project["name"]}</p>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🔍 Scout", "📥 Ingest", "📚 Library", "🧾 Export", "✍️ Synthesis"])
    
    # 🔍 SCOUT
    with tabs[0]:
        st.markdown('<div class="res-card"><h3>Global Intelligence Scout</h3><p>Query Global Graphs and Web Frontiers.</p></div>', unsafe_allow_html=True)
        q = st.text_input("Intelligence Objective")
        col1, col2 = st.columns(2)
        grey = col1.toggle("Grey Literature")
        pilot = col2.toggle("Auto-Pilot")
        
        if st.button("🚀 Execute Loop", use_container_width=True):
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
                        st.markdown(f"<div class='res-card' style='padding:15px; border-left-color:#F97316;'><b>{p['title']}</b> ({p.get('year','n.a')})</div>", unsafe_allow_html=True)
                        if st.button("Save to Archive", key=f"s_{p['title']}"):
                            db.table("papers").insert({
                                "project_id": st.session_state.project_id,
                                "title": p['title'], "authors": [a.get('name','Anon') for a in p.get('authors',[])],
                                "year": p.get('year'), "abstract": p.get('abstract'), "url": p.get('url'), "source_type": "scout"
                            }).execute()
                            st.toast("Saved!")
                status.update(label="Loop Complete", state="complete")

    # 📥 INGEST
    with tabs[1]:
        st.markdown('<div class="res-card"><h3>Digital Archive Ingest</h3><p>Upload PDFs or Scrape URLs with Agentic Extraction.</p></div>', unsafe_allow_html=True)
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

    # 🧾 EXPORT
    with tabs[3]:
        st.markdown('<div class="res-card"><h3>Intelligence Export Lounge</h3></div>', unsafe_allow_html=True)
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

    # ✍️ SYNTHESIS
    with tabs[4]:
        st.markdown('<div class="res-card"><h3>Agentic Synthesis Engine</h3><p>Grounded strictly in project archives.</p></div>', unsafe_allow_html=True)
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
