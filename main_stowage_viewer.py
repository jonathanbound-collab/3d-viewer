# main_stowage_viewer.py

import pandas as pd
import plotly.graph_objects as go
import plotly.offline as pyo
import sys
from IPython.display import display, HTML

# ---------- constants ----------
REQUIRED_COLUMNS = ["Bay", "Row", "Tier", "Container_ID", "Container_Location", "Declared_Cargo", "Colour"]

# ---------- helpers ----------
def row_to_y(row):
    """Converts ship row numbering to Cartesian Y-coordinates."""
    try:
        r = int(row)
        if r == 0: return 0
        steps = (r + 1) // 2
        sign = 1 if r % 2 == 1 else -1
        return sign * steps
    except (ValueError, TypeError):
        return None

def calculate_dimensions(bay):
    """Calculates a container's x-position and length based on its bay number."""
    if bay % 2 == 0:  # 40ft container (EVEN bay)
        x_start = (bay - 2) / 2
        length = 2.0
    else:  # 20ft container (ODD bay)
        x_start = (bay - 1) / 2
        length = 1.0
    return x_start, length

def create_container_traces(x, y, z, length, width, height, color, hovertext):
    """Creates traces for a container's solid faces and wireframe edges."""
    vertices = {
        'x': [x, x + length, x + length, x, x, x + length, x + length, x],
        'y': [y, y, y + width, y + width, y, y, y + width, y + width],
        'z': [z, z, z, z, z + height, z + height, z + height, z + height]
    }

    face_mesh = go.Mesh3d(
        x=vertices['x'], y=vertices['y'], z=vertices['z'],
        i = [0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3],
        j = [1, 3, 5, 7, 4, 7, 2, 6, 3, 7, 4, 5],
        k = [2, 2, 6, 6, 7, 3, 6, 5, 7, 6, 5, 1],
        color=color,
        opacity=1.0,
        hoverinfo="text",
        text=hovertext,
        flatshading=True,
        lighting=dict(
            ambient=0.8,
            diffuse=0.2,
            specular=0.0
        )
    )

    path_indices = [0,1,2,3,0, None, 4,5,6,7,4, None, 0,4, None, 1,5, None, 2,6, None, 3,7]
    edge_x, edge_y, edge_z = [], [], []
    for i in path_indices:
        if i is None:
            edge_x.append(None)
            edge_y.append(None)
            edge_z.append(None)
        else:
            edge_x.append(vertices['x'][i])
            edge_y.append(vertices['y'][i])
            edge_z.append(vertices['z'][i])

    edge_wireframe = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode='lines',
        line=dict(color='black', width=2),
        hoverinfo='none'
    )
    
    return [face_mesh, edge_wireframe]


def main(csv_path, output_path):
    """Main function to load data, create the plot, and save it."""
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: The file '{csv_path}' was not found.")
        sys.exit(1)

    if not all(col in df.columns for col in REQUIRED_COLUMNS):
        print(f"Error: CSV must contain the following columns: {REQUIRED_COLUMNS}")
        sys.exit(1)

    df.dropna(subset=["Bay", "Row", "Tier"], inplace=True)

    fig = go.Figure()
    print(f"Processing {len(df)} containers...")

    for _, c in df.iterrows():
        try:
            bay = int(c["Bay"])
            y = row_to_y(c["Row"])
            z = int(c["Tier"]) - 1
            if y is None:
                print(f"Warning: Skipping container {c['Container_ID']} due to invalid 'Row' value: {c['Row']}")
                continue
            x_start, length = calculate_dimensions(bay)
            hover_text = (
                f"<b>ID:</b> {c['Container_ID']}<br>"
                f"<b>Location:</b> {c['Container_Location']}<br>"
                f"<b>Cargo:</b> {c['Declared_Cargo']}"
            )
            
            container_traces = create_container_traces(
                x=x_start, y=y, z=z,
                length=length, width=1.0, height=1.0,
                color=c["Colour"],
                hovertext=hover_text
            )
            for trace in container_traces:
                fig.add_trace(trace)

        except (ValueError, TypeError) as e:
            print(f"Warning: Skipping container {c['Container_ID']} due to a data error: {e}")
            continue

    # --- NEW: Prepare Custom Axis Ticks ---
    # Bay (X-axis): Label the 40ft bay slots
    even_bays = sorted([b for b in df['Bay'].unique() if b % 2 == 0])
    bay_tickvals = [(b - 2) / 2 for b in even_bays]
    bay_ticktext = [f"{b:02d}" for b in even_bays] # Format as 02, 06, etc.

    # Tier (Z-axis)
    unique_tiers = sorted(df['Tier'].unique())
    tier_tickvals = [t - 1 for t in unique_tiers]
    tier_ticktext = [str(t) for t in unique_tiers]

    # Row (Y-axis)
    unique_rows = sorted(df['Row'].unique())
    row_tickvals = [row_to_y(r) for r in unique_rows]
    row_ticktext = [str(r) for r in unique_rows]

    # --- UPDATED: Configure and Save Plot ---
    fig.update_layout(
        title='Vessel Stowage Plan',
        showlegend=False, # <-- Hide the legend
        scene=dict(
            # Define axes with custom ticks
            xaxis=dict(title="Bay", tickvals=bay_tickvals, ticktext=bay_ticktext),
            yaxis=dict(title="Row", tickvals=row_tickvals, ticktext=row_ticktext),
            zaxis=dict(title="Tier", tickvals=tier_tickvals, ticktext=tier_ticktext),
            aspectmode="data",
            camera=dict(eye=dict(x=1.8, y=-1.8, z=1.5))
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )

    pyo.plot(fig, filename=output_path, auto_open=False)
    print(f"✨ Successfully created stowage view at '{output_path}'")


if __name__ == "__main__":
    # --- For Notebook Users: Define your files here ---
    input_csv = "containers.csv"
    output_html = "stowage_view.html"
    
    print(f"Running analysis for '{input_csv}'...")
    main(input_csv, output_html)

    print("Displaying stowage plan...")
    with open(output_html, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    display(HTML(html_content))