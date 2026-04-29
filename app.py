"""
app.py
======
Main entry point for the WC Knowledge Graph demo.
Sets up the driver, page config, and sidebar navigation.
"""

import streamlit as st
from neo4j import GraphDatabase
import os
from streamlit_agraph import agraph, Node, Edge, Config

# Page Config
st.set_page_config(
    page_title="WC Claims Intelligence",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Neo4j Driver Setup
@st.cache_resource
def get_driver():
    try:
        uri = st.secrets["neo4j"]["uri"]
        user = st.secrets["neo4j"]["user"]
        password = st.secrets["neo4j"]["password"]
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        return driver
    except Exception as e:
        st.error(f"Failed to connect to Neo4j. Check secrets.toml. Error: {e}")
        return None

driver = get_driver()

if not driver:
    st.stop()

# Visual Design System Config
NODE_COLORS = {
    "Claim": "#4A90A4",
    "Claimant": "#F5A623",
    "Adjuster": "#58D68D",
    "Provider": "#48C9B0",
    "Attorney": "#E74C3C",
    "Employer": "#95A5A6",
    "Policy": "#9B59B6",
    "ClaimEvent": "#F7DC6F",
    "Stage": "#D5DBDB",
    "ReserveSnapshot": "#85C1E9"
}

def render_graph(nodes_data, edges_data, title="Graph"):
    """Helper to render streamlit-agraph."""
    nodes = []
    edges = []
    
    for n in nodes_data:
        nodes.append(Node(
            id=n["id"],
            label=n["label"],
            size=n.get("size", 25),
            color=NODE_COLORS.get(n.get("type", "Claim"), "#999999"),
            shape=n.get("shape", "dot")
        ))
        
    for e in edges_data:
        edges.append(Edge(
            source=e["source"],
            label=e["label"],
            target=e["target"],
            color=e.get("color", "#CCCCCC"),
            width=e.get("width", 1)
        ))
        
    config = Config(width=1000, height=400, directed=True, 
                    physics=True, hierarchical=False)
                    
    return agraph(nodes=nodes, edges=edges, config=config)

# Sidebar
with st.sidebar:
    st.title("🕸️ Claims Intelligence")
    st.markdown("Knowledge Graph Analytics")
    st.divider()
    
    # st.page_link does not need to be called if we rely on the default multipage 
    # folder structure. We'll let Streamlit's native 'pages/' handle navigation.
    st.info("Select a module above.")

st.title("Welcome to WC Claims Intelligence")
st.markdown("""
Please navigate using the sidebar.
- **Portfolio Overview**: Executive dashboard and claim search.
- **Similarity Workbench**: Predictive similarity analysis and scenario exploration.
- **Admin**: Database generation and schema verification.
""")
