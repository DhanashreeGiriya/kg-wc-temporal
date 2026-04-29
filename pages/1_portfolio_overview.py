import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app import get_driver, render_graph
from graph_queries import get_portfolio_kpis, get_claim_grid, get_claim_trajectory, get_entity_neighborhood, get_reserve_history

st.set_page_config(page_title="Portfolio Overview", layout="wide")
driver = get_driver()

st.title("Portfolio Overview")

# Top KPIs
kpis = get_portfolio_kpis(driver)
if kpis:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Claims", kpis.get("total_claims", 0))
    col2.metric("Open Claims", kpis.get("open_claims", 0))
    
    reserves = kpis.get("total_reserves", 0)
    res_str = f"${reserves/1000000:.1f}M" if reserves > 1000000 else f"${reserves/1000:.0f}K"
    col3.metric("Outstanding Reserves", res_str)
    
    col4.metric("Stale (>180d)", kpis.get("stale_claims", 0))
    col5.metric("In Dispute", kpis.get("dispute_claims", 0))

st.divider()

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    status_filter = st.radio("Status", ["All", "OPEN", "CLOSED"], index=1)

# Claim Grid
claims_data = get_claim_grid(driver, status_filter, limit=100)
if not claims_data:
    st.warning("No claims found. Go to Admin to generate data.")
    st.stop()

df = pd.DataFrame(claims_data)
# Reorder columns and format
df = df[["claim_id", "status", "body_part", "current_stage", "total_paid", "current_reserve", "is_hero", "demo_notes"]]

st.subheader("Claim Roster")
st.dataframe(
    df, 
    use_container_width=True,
    column_config={
        "total_paid": st.column_config.NumberColumn(format="$%d"),
        "current_reserve": st.column_config.NumberColumn(format="$%d"),
        "is_hero": st.column_config.CheckboxColumn("Hero")
    }
)

st.divider()
st.subheader("Claim Deep Dive")

# Pick a claim to deep dive
selected_claim = st.selectbox("Select a Claim ID", df["claim_id"].tolist())

if selected_claim:
    traj = get_claim_trajectory(driver, selected_claim)
    reserves = get_reserve_history(driver, selected_claim)
    hood = get_entity_neighborhood(driver, selected_claim)
    
    col_chart, col_graph = st.columns([2, 1])
    
    with col_chart:
        st.markdown("**Trajectory Gantt**")
        if traj:
            # Convert to gantt format
            gantt_data = []
            for e in traj:
                gantt_data.append({
                    "Task": selected_claim,
                    "Start": e["date"],
                    "Duration": e["duration"],
                    "Stage": e["stage_label"],
                    "Phase": e["phase"]
                })
            
            # Simple plotly timeline (approximate using duration as end time)
            df_g = pd.DataFrame(gantt_data)
            df_g["Start"] = pd.to_datetime(df_g["Start"])
            df_g["End"] = df_g["Start"] + pd.to_timedelta(df_g["Duration"], unit='D')
            
            fig = px.timeline(df_g, x_start="Start", x_end="End", y="Task", color="Phase", hover_name="Stage")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
            
        st.markdown("**Reserve Staircase**")
        if reserves:
            df_r = pd.DataFrame(reserves)
            fig2 = px.line(df_r, x="date", y="amount", markers=True, text="trigger_stage", title="Reserve Evolution")
            fig2.update_traces(textposition="top left")
            st.plotly_chart(fig2, use_container_width=True)
            
    with col_graph:
        st.markdown("**Entity Neighborhood**")
        nodes = [{"id": selected_claim, "label": selected_claim, "type": "Claim", "shape": "dot"}]
        edges = []
        
        if hood.get("claimant"):
            nodes.append({"id": hood["claimant"], "label": hood["claimant"], "type": "Claimant", "shape": "dot"})
            edges.append({"source": selected_claim, "target": hood["claimant"], "label": "HAS_CLAIMANT"})
            
        if hood.get("adjuster"):
            nodes.append({"id": hood["adjuster"], "label": hood["adjuster"], "type": "Adjuster", "shape": "dot"})
            edges.append({"source": selected_claim, "target": hood["adjuster"], "label": "ASSIGNED_TO"})
            
        if hood.get("employer"):
            nodes.append({"id": hood["employer"], "label": hood["employer"], "type": "Employer", "shape": "dot"})
            edges.append({"source": selected_claim, "target": hood["employer"], "label": "OCCURRED_AT"})
            
        if hood.get("attorney"):
            nodes.append({"id": hood["attorney"], "label": hood["attorney"], "type": "Attorney", "shape": "dot"})
            edges.append({"source": selected_claim, "target": hood["attorney"], "label": "REPRESENTED_BY"})
            
        for p in hood.get("providers", []):
            nodes.append({"id": p, "label": p, "type": "Provider", "shape": "dot"})
            edges.append({"source": selected_claim, "target": p, "label": "TREATED_BY"})
            
        render_graph(nodes, edges)

