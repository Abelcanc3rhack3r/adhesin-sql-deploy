import streamlit as st
import os
import requests
import pandas as pd
import py3Dmol
from stmol import showmol

st.set_page_config(page_title="Protein DB Viewer", layout="wide")
st.title("🧬 Adhesin  Like Protein Database")

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# 1. INITIALIZE SESSION STATE
if "results" not in st.session_state:
    st.session_state.results = []
if "colors" not in st.session_state:
    st.session_state.colors = {"RBH": "#FF4B4B", "ABD": "#1E90FF", "MAD": "#00FA9A", "OTHER": "#FFA500"}
if "target_id" not in st.session_state:
    st.session_state.target_id = None
if "query_performed" not in st.session_state:
    st.session_state.query_performed = False

# 2. SIDEBAR: AI QUERY BOX
st.sidebar.header("✨ AI Query")
nl_query = st.sidebar.text_area("Natural Language Query:", placeholder="Color ABD red and show stad-1")

if st.sidebar.button("Run AI Query"):
    with st.spinner("Gemini is analyzing..."):
        st.session_state.query_performed = True
        try:
            res = requests.post(f"{API_URL}/nl_ask", json={"query": nl_query})
            if res.status_code == 200:
                data = res.json()
                st.session_state.results = data.get("results", [])
                st.session_state.target_id = data.get("target_protein")
                st.session_state.colors.update(data.get("color_rules", {}))
            else:
                st.error(f"Backend Error: {res.text}")
        except Exception as e:
            st.error(f"Could not connect to backend: {e}")

st.sidebar.markdown("---")

# 3. SIDEBAR: MANUAL SEARCH
st.sidebar.header("Manual Search")
search_query = st.sidebar.text_input("Search (ID, Species, Annotation):", "")
if st.sidebar.button("Manual Search"):
    st.session_state.query_performed = True
    st.session_state.target_id = None 
    res = requests.get(f"{API_URL}/search", params={"query": search_query})
    if res.status_code == 200:
        st.session_state.results = res.json()

# 4. RENDER RESULTS OR PLACEHOLDERS
if st.session_state.results:
    df = pd.DataFrame(st.session_state.results)
    st.write(f"### Found {len(df)} results")
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Interactive 3D Domain Viewer")
    
    prot_list = df['protein_id'].tolist()
    default_idx = prot_list.index(st.session_state.target_id) if st.session_state.target_id in prot_list else 0
    selected_id = st.selectbox("Select Protein:", prot_list, index=default_idx)
    
    if selected_id:
        col1, col2 = st.columns(2)
        res = requests.get(f"{API_URL}/structure/{selected_id}")
        dom_res = requests.get(f"{API_URL}/domains/{selected_id}")
        dom_df = pd.DataFrame(dom_res.json()) if dom_res.status_code == 200 else pd.DataFrame()

        if res.status_code == 200:
            with col1:
                pdb_string = res.json()
                ext = "cif" if "data_" in pdb_string[:500] else "pdb"
                view = py3Dmol.view(width=800, height=600)
                view.addModel(pdb_string, ext)
                view.setStyle({'cartoon': {'color': '#d3d3d3'}})
                
                if not dom_df.empty:
                    for _, row in dom_df.iterrows():
                        d_class = row['class_name'].upper()
                        color = st.session_state.colors.get(d_class, "#9C27B0")
                        view.addStyle({'resi': f"{row['res_start']}-{row['res_end']}"}, {'cartoon': {'color': color}})
                
                view.zoomTo()
                view.setBackgroundColor('white')
                showmol(view, height=600, width=800)
                
            with col2:
                st.write("#### Domain Map")
                if not dom_df.empty:
                    st.dataframe(dom_df[['class_name', 'res_start', 'res_end']], use_container_width=True)
                    st.write("**Legend:**")
                    for d_class, color in st.session_state.colors.items():
                        st.markdown(f"<h5 style='color:{color}'>■ {d_class}</h5>", unsafe_allow_html=True)

# THE NEW PLACEHOLDER LOGIC
elif st.session_state.query_performed:
    st.warning("⚠️ No rows returned. Try adjusting your query or keywords.")
else:
    st.info("👈 Use the AI box or manual search to begin.")
