import streamlit as st
import pandas as pd
from app import get_driver
import subprocess
import sys
import threading

st.set_page_config(page_title="Admin & Schema", layout="wide")
driver = get_driver()

st.title("Admin & Data Management")

def get_stats():
    q = """
    CALL db.labels() YIELD label
    CALL apoc.cypher.run('MATCH (:`'+label+'`) RETURN count(*) as count', {}) YIELD value
    RETURN label, value.count as count
    ORDER BY count DESC
    """
    # AuraDB Free doesn't have APOC, so fallback to manual querying
    try:
        with driver.session() as s:
            labels = [r["label"] for r in s.run("CALL db.labels() YIELD label RETURN label")]
            stats = []
            for l in labels:
                c = s.run(f"MATCH (n:`{l}`) RETURN count(n) AS c").single()["c"]
                stats.append({"Label": l, "Count": c})
            return stats
    except Exception:
        return []

col1, col2 = st.columns([1, 1])

with col1:
    st.header("Database Statistics")
    stats = get_stats()
    if stats:
        st.dataframe(pd.DataFrame(stats), use_container_width=True)
    else:
        st.info("No data or unable to fetch stats.")
        
    st.divider()
    st.header("Schema Visualization")
    st.image("https://raw.githubusercontent.com/neo4j-graph-examples/recommendations/main/img/datamodel.png", caption="Placeholder Schema Diagram (Reference)")
    # Since apoc.meta.graph is unavailable in AuraDB Free, we use a placeholder or describe it.

with col2:
    st.header("Actions")
    
    st.warning("⚠️ These actions will modify the database.")
    
    if st.button("1. Clear Database"):
        with st.spinner("Deleting all nodes and relationships..."):
            with driver.session() as s:
                s.run("MATCH (n) DETACH DELETE n")
            st.success("Database cleared!")
            st.rerun()
            
    if st.button("2. Generate Synthetic Data (~400 claims)"):
        with st.spinner("Running scenario_data_generator.py... This takes about 30 seconds."):
            try:
                # We can import and run, or subprocess
                from scenario_data_generator import WCDataGenerator
                gen = WCDataGenerator()
                gen.clear_database()
                gen.run_all()
                gen.close()
                st.success("Data generated successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Generation failed: {e}")
                
    if st.button("3. Compute Pairwise Similarity"):
        with st.spinner("Running similarity_engine.py... This computes LCS, DTW, and Jaccard for all pairs. Takes ~60 seconds."):
            try:
                from similarity_engine import SimilarityEngine
                sim = SimilarityEngine()
                sim.compute_all_pairs()
                sim.close()
                st.success("Similarity edges persisted successfully!")
            except Exception as e:
                st.error(f"Computation failed: {e}")

st.divider()
st.subheader("Schema Constraints")
with open("schema.cypher", "r") as f:
    st.code(f.read(), language="cypher")
