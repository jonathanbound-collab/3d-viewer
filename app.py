# app.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import StringIO

# Import the helper functions from your other file
from main_stowage_viewer import (
    REQUIRED_COLUMNS,
    row_to_y,
    calculate_dimensions,
    create_container_traces
)

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Stowage Viewer")
st.title("🚢 3D Stowage Plan Visualizer")

# --- Layout ---
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Container Data")
    st.info("Upload a CSV file or paste your data below.")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    pasted_data = st.text_area(
        "Or paste CSV data here:",
        height=300,
        placeholder="Bay,Row,Tier,Container_ID,...\n01,01,82,MSKU123456,..."
    )

    # Determine the data source
    data_source = uploaded_file if uploaded_file else pasted_data

with col2:
    st.header("3D Visualization")

    if data_source:
        try:
            # Read the data into a pandas DataFrame
            if isinstance(data_source, str):
                df = pd.read_csv(StringIO(data_source))
            else:  # It's an uploaded file
                df = pd.read_csv(data_source)

            # --- This is the core logic from your main_stowage_viewer.py ---
            if not all(col in df.columns for col in REQUIRED_COLUMNS):
                st.error(f"Error: CSV must contain the columns: {REQUIRED_COLUMNS}")
            else:
                df.dropna(subset=["Bay", "Row", "Tier"], inplace=True)
                fig = go.Figure()

                for _, c in df.iterrows():
                    bay = int(c["Bay"])
                    y = row_to_y(c["Row"])
                    z = int(c["Tier"]) - 1
                    x_start, length = calculate_dimensions(bay)
                    hover_text = (
                        f"<b>ID:</b> {c['Container_ID']}<br>"
                        f"<b>Location:</b> {c['Container_Location']}<br>"
                        f"<b>Cargo:</b> {c['Declared_Cargo']}"
                    )
                    traces = create_container_traces(
                        x=x_start, y=y, z=z,
                        length=length, width=1.0, height=1.0,
                        color=c["Colour"],
                        hovertext=hover_text
                    )
                    for trace in traces:
                        fig.add_trace(trace)
                
                # Prepare custom axis ticks
                even_bays = sorted([b for b in df['Bay'].unique() if b % 2 == 0])
                bay_tickvals = [(b - 2) / 2 for b in even_bays]
                # --- MODIFIED LINE ---
                bay_ticktext = [f"{int(b):02d}" for b in even_bays] # Convert to int before formatting

                unique_tiers = sorted(df['Tier'].unique())
                tier_tickvals = [t - 1 for t in unique_tiers]
                tier_ticktext = [str(t) for t in unique_tiers]
                unique_rows = sorted(df['Row'].unique())
                row_tickvals = [row_to_y(r) for r in unique_rows]
                row_ticktext = [str(r) for r in unique_rows]

                fig.update_layout(
                    title='Vessel Stowage Plan',
                    showlegend=False,
                    scene=dict(
                        xaxis=dict(title="Bay", tickvals=bay_tickvals, ticktext=bay_ticktext),
                        yaxis=dict(title="Row", tickvals=row_tickvals, ticktext=row_ticktext),
                        zaxis=dict(title="Tier", tickvals=tier_tickvals, ticktext=tier_ticktext),
                        aspectmode="data",
                        camera=dict(eye=dict(x=1.8, y=-1.8, z=1.5))
                    ),
                    margin=dict(l=0, r=0, b=0, t=40)
                )

                # Display the final plot
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"An error occurred while processing the data: {e}")
    else:
        st.info("Upload or paste data to see the visualization.")
