"""
Interactive Dash Dashboard with H3 + Offline Folium
- Time slider to select hour
- Left map: H3 cells colored by density
- Right map: H3 cells colored by score (0-1, blue to red via white)

Configuration:
  THRESHOLD - Controls where white appears in the score colormap (default: 0.5)
              Values below threshold are blue, above are red, at threshold is white

Requirements:
  pip install dash pandas numpy h3 offline-folium

Setup (one-time, requires internet):
  python -m offline_folium  # Downloads assets for offline use

Run:
  python dash_h3_dashboard.py

Then open browser to: http://127.0.0.1:8050
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import h3
import tempfile
from pathlib import Path
from datetime import datetime

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

from offline_folium import OfflineMap
import folium


# ============================================================================
# CONFIGURATION
# ============================================================================
THRESHOLD = 0.5  # Adjust this to change where white appears in score map (0.0 to 1.0)


def h3_cell_to_geojson_polygon(cell: str) -> dict:
    """Convert H3 cell to GeoJSON polygon."""
    boundary_latlng = h3.cell_to_boundary(cell)
    coords_lnglat = [(lng, lat) for (lat, lng) in boundary_latlng]
    if coords_lnglat[0] != coords_lnglat[-1]:
        coords_lnglat.append(coords_lnglat[0])
    return {
        "type": "Feature",
        "properties": {"h3": cell},
        "geometry": {"type": "Polygon", "coordinates": [coords_lnglat]},
    }


def create_density_map(df_hour: pd.DataFrame, center_lat: float, center_lng: float) -> str:
    """Create folium map colored by density."""
    m = OfflineMap(
        location=[center_lat, center_lng],
        zoom_start=6,
        tiles="CartoDB positron",
        control_scale=True,
    )
    
    if len(df_hour) == 0:
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
        m.save(temp_file.name)

        return temp_file.name
    
    vmin = df_hour['density'].min()
    vmax = df_hour['density'].max()
    
    # Create colormap once and use for both hexagons and legend
    from branca.colormap import LinearColormap
    
    # Plasma-like colormap
    colors = ['#0d0887', '#6400c8', '#b42c8c', '#f07030', '#fce225']
    colormap = LinearColormap(
        colors=colors,
        vmin=vmin,
        vmax=vmax,
        caption='Density'
    )
    
    # Add hexagons
    for _, row in df_hour.iterrows():
        cell = row['h3_cell']
        density = row['density']
        
        feature = h3_cell_to_geojson_polygon(cell)
        fill_color = colormap(density)  # Use branca colormap to get color
        
        folium.GeoJson(
            feature,
            style_function=lambda feat, color=fill_color: {
                "color": "#444444",
                "weight": 1,
                "fillColor": color,
                "fillOpacity": 0.6,
            },
            tooltip=folium.Tooltip(f"H3: {cell}<br>Density: {density:.2f}"),
        ).add_to(m)
    
    # Add the colorbar legend
    colormap.add_to(m)
    
    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
    m.save(temp_file.name)
    return temp_file.name


def create_score_map(df_hour: pd.DataFrame, center_lat: float, center_lng: float) -> str:
    """Create folium map colored by score (0-1, blue to red via white)."""
    m = OfflineMap(
        location=[center_lat, center_lng],
        zoom_start=6,
        tiles="OpenStreetMap",
        control_scale=True,
    )
    
    if len(df_hour) == 0:
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
        m.save(temp_file.name)
        return temp_file.name
    
    # Create colormap once and use for both hexagons and legend
    from branca.colormap import LinearColormap
    
    colors = ['#0000ff', '#ffffff', '#ff0000']
    index = [0.0, THRESHOLD, 1.0]
    
    colormap = LinearColormap(
        colors=colors,
        index=index,
        vmin=0.0,
        vmax=1.0,
        caption=f'Score (white at {THRESHOLD})'
    )
    
    # Add hexagons
    for _, row in df_hour.iterrows():
        cell = row['h3_cell']
        score = row['score']
        truth = row.get('truth', 0)  # Default to 0 if column doesn't exist
        
        feature = h3_cell_to_geojson_polygon(cell)
        fill_color = colormap(score)  # Use branca colormap to get color
        
        folium.GeoJson(
            feature,
            style_function=lambda feat, color=fill_color: {
                "color": "#444444",
                "weight": 1,
                "fillColor": color,
                "fillOpacity": 0.6,
            },
            tooltip=folium.Tooltip(f"H3: {cell}<br>Score: {score:.3f}<br>Truth: {truth}"),
        ).add_to(m)
    
    # Add star markers for truth=1 cells
    #from folium.plugins import BeautifyIcon
    
    truth_cells = df_hour[df_hour['truth'] == 1]
    for _, row in truth_cells.iterrows():
        cell = row['h3_cell']
        lat, lng = h3.cell_to_latlng(cell)
        
        folium.CircleMarker(
            location=[lat, lng],
            radius=3,
            color='red',
            weight=1,
            fill=True,
            fillColor='red',
            fillOpacity=1.0,
            tooltip=f"Truth=1<br>H3: {cell}<br>Score: {row['score']:.3f}"
        ).add_to(m)

        # Use BeautifyIcon for a clean star marker
        # icon = BeautifyIcon(
        #     icon='star',
        #     icon_shape='circle',  # Flat circle, not a pin
        #     border_color='black',
        #     border_width=2,
        #     background_color='yellow',
        #     text_color='black'
        # )
        
        # folium.Marker(
        #     location=[lat, lng],
        #     icon=icon,
        #     tooltip=f"Truth=1<br>H3: {cell}<br>Score: {row['score']:.3f}"
        # ).add_to(m)
    
    # Add the colorbar legend
    colormap.add_to(m)
    
    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
    m.save(temp_file.name)
    return temp_file.name


# ============================================================================
# SAMPLE DATA GENERATION (replace with your actual data loading)
# ============================================================================

def create_sample_data() -> pd.DataFrame:
    """
    Create sample data - REPLACE THIS with your actual data loading.
    
    Expected columns:
    - hour: timestamp string (format: YYYY-MM-DD_HH)
    - h3_cell: H3 cell index
    - score: float (0-1)
    - density: float (no upper bound)
    - truth: int (0 or 1) - marks cells with truth=1 with a star on map 2
    """
    np.random.seed(42)
    
    # Generate sample hours
    hours = pd.date_range('2024-01-01', periods=24, freq='h')
    
    # Center around Denver
    center_lat, center_lng = 39.7392, -104.9903
    center_cell = h3.latlng_to_cell(center_lat, center_lng, 3)  # Resolution 3
    
    # Get surrounding cells
    cells = list(h3.grid_disk(center_cell, 2))
    
    data = []
    for hour in hours:
        for cell in cells:
            # Random data for each cell at each hour
            data.append({
                'hour': hour.strftime('%Y-%m-%d_%H'),
                'h3_cell': cell,
                'score': np.random.random(),  # 0-1
                'density': np.random.exponential(scale=50),  # Positive, no upper bound
                'truth': np.random.choice([0, 1], p=[0.7, 0.3]),  # 70% zeros, 30% ones
            })
    
    return pd.DataFrame(data)


# ============================================================================
# DASH APP
# ============================================================================

# Load data
df = create_sample_data()  # REPLACE with: df = pd.read_csv('your_data.csv')

# Get unique hours for slider
hours = sorted(df['hour'].unique())
hour_marks = {i: hours[i] for i in range(0, len(hours), max(1, len(hours)//10))}

# Calculate map center from data
first_cell = df['h3_cell'].iloc[0]
center_lat, center_lng = h3.cell_to_latlng(first_cell)

# Initialize Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("H3 Dashboard - Density & Score Maps", 
            style={'textAlign': 'center', 'marginBottom': 20}),
    
    # Time slider
    html.Div([
        html.Label("Select Hour:", style={'fontSize': 18, 'fontWeight': 'bold'}),
        dcc.Slider(
            id='hour-slider',
            min=0,
            max=len(hours) - 1,
            value=0,
            marks=hour_marks,
            step=1,
            tooltip={"placement": "bottom", "always_visible": True},
        ),
        html.Div(id='selected-hour', 
                style={'textAlign': 'center', 'fontSize': 16, 'marginTop': 10})
    ], style={'padding': '20px', 'marginBottom': 20}),
    
    # Maps side by side
    html.Div([
        # Density map (left)
        html.Div([
            html.H3("Density Map", style={'textAlign': 'center'}),
            html.Iframe(
                id='density-map',
                srcDoc='',
                width='100%',
                height='600px',
                style={'border': '2px solid #ddd', 'borderRadius': '5px'}
            ),
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        
        # Score map (right)
        html.Div([
            html.H3("Score Map (0=Green, 1=Red)", style={'textAlign': 'center'}),
            html.Iframe(
                id='score-map',
                srcDoc='',
                width='100%',
                height='600px',
                style={'border': '2px solid #ddd', 'borderRadius': '5px'}
            ),
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%'}),
    ]),
], style={'padding': '20px', 'fontFamily': 'Arial, sans-serif'})


@app.callback(
    [Output('selected-hour', 'children'),
     Output('density-map', 'srcDoc'),
     Output('score-map', 'srcDoc')],
    [Input('hour-slider', 'value')]
)
def update_maps(hour_idx):
    """Update both maps when slider changes."""
    selected_hour = hours[hour_idx]
    # Filter data for selected hour
    df_hour = df[df['hour'] == selected_hour].copy()

    print(f"Hour: {selected_hour}, Rows: {len(df_hour)}")  # Add this
    print(f"Sample data:\n{df_hour.head()}")  # Add this
    
    # Create maps
    density_path = create_density_map(df_hour, center_lat, center_lng)
    score_path = create_score_map(df_hour, center_lat, center_lng)

    print(f"Density map path: {density_path}")
    print(f"Score map path: {score_path}")
    
    # Read HTML content
    with open(density_path, 'r', encoding='utf-8') as f:
        density_html = f.read()
    
    with open(score_path, 'r', encoding='utf-8') as f:
        score_html = f.read()
    
    return (
        f"Showing data for: {selected_hour} ({len(df_hour)} cells)",
        density_html,
        score_html
    )


if __name__ == '__main__':
    print("Starting Dash app...")
    print("Open browser to: http://127.0.0.1:8050")
    print("\nMake sure you've run: python -m offline_folium")
    print("to download offline assets first!\n")
    app.run(debug=True, port=8050)