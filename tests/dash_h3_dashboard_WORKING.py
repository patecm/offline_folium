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


def create_colormap_density(value: float, vmin: float, vmax: float) -> str:
    """Create plasma-like colormap for density (purple -> pink -> orange -> yellow)."""
    if vmax <= vmin:
        t = 0.5
    else:
        t = (value - vmin) / (vmax - vmin)
    t = float(np.clip(t, 0.0, 1.0))
    
    # Plasma colormap approximation
    # Dark purple -> bright purple -> pink -> orange -> yellow
    if t < 0.25:
        # Dark purple to bright purple
        s = t * 4
        r = int(13 + s * (100 - 13))
        g = int(8 + s * (0 - 8))
        b = int(135 + s * (200 - 135))
    elif t < 0.5:
        # Bright purple to pink
        s = (t - 0.25) * 4
        r = int(100 + s * (180 - 100))
        g = int(0 + s * (55 - 0))
        b = int(200 + s * (130 - 200))
    elif t < 0.75:
        # Pink to orange
        s = (t - 0.5) * 4
        r = int(180 + s * (240 - 180))
        g = int(55 + s * (100 - 55))
        b = int(130 + s * (25 - 130))
    else:
        # Orange to yellow
        s = (t - 0.75) * 4
        r = int(240 + s * (252 - 240))
        g = int(100 + s * (230 - 100))
        b = int(25 + s * (37 - 25))
    
    return f"#{r:02x}{g:02x}{b:02x}"


def create_colormap_score(value: float, threshold: float = THRESHOLD) -> str:
    """
    Create seismic-like colormap for score (blue -> white -> red).
    
    Args:
        value: Score value (0-1)
        threshold: Where white appears (default: THRESHOLD global setting)
    """
    # Clamp to 0-1
    v = float(np.clip(value, 0.0, 1.0))
    
    # Seismic: blue (0) -> white (threshold) -> red (1)
    if v < threshold:
        # Blue to White
        if threshold > 0:
            t = v / threshold
        else:
            t = 0
        r = int(0 + t * 255)
        g = int(0 + t * 255)
        b = int(255)
    else:
        # White to Red
        if threshold < 1:
            t = (v - threshold) / (1.0 - threshold)
        else:
            t = 0
        r = int(255)
        g = int(255 - t * 255)
        b = int(255 - t * 255)
    
    return f"#{r:02x}{g:02x}{b:02x}"


def create_density_map(df_hour: pd.DataFrame, center_lat: float, center_lng: float) -> str:
    """Create folium map colored by density."""
    m = OfflineMap(
        location=[center_lat, center_lng],
        zoom_start=6,
        tiles="CartoDB positron",
        control_scale=True,
    )
    
    if len(df_hour) == 0:
        m.save("temp_density_map.html")
        return "temp_density_map.html"
    
    vmin = df_hour['density'].min()
    vmax = df_hour['density'].max()
    
    # Add hexagons
    for _, row in df_hour.iterrows():
        cell = row['h3_cell']
        density = row['density']
        
        feature = h3_cell_to_geojson_polygon(cell)
        fill_color = create_colormap_density(density, vmin, vmax)
        
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
    
    # Save to temp file
    m.save("temp_density_map.html")
    return "temp_density_map.html"


def create_score_map(df_hour: pd.DataFrame, center_lat: float, center_lng: float) -> str:
    """Create folium map colored by score (0-1, blue to red via white)."""
    m = OfflineMap(
        location=[center_lat, center_lng],
        zoom_start=6,
        tiles="CartoDB positron",
        control_scale=True,
    )
    
    if len(df_hour) == 0:
        m.save("temp_score_map.html")
        return "temp_score_map.html"
    
    # Add hexagons
    for _, row in df_hour.iterrows():
        cell = row['h3_cell']
        score = row['score']
        
        feature = h3_cell_to_geojson_polygon(cell)
        fill_color = create_colormap_score(score)
        
        folium.GeoJson(
            feature,
            style_function=lambda feat, color=fill_color: {
                "color": "#444444",
                "weight": 1,
                "fillColor": color,
                "fillOpacity": 0.6,
            },
            tooltip=folium.Tooltip(f"H3: {cell}<br>Score: {score:.3f}"),
        ).add_to(m)
    
    # Save to temp file
    m.save("temp_score_map.html")
    return "temp_score_map.html"


# ============================================================================
# SAMPLE DATA GENERATION (replace with your actual data loading)
# ============================================================================

def create_sample_data() -> pd.DataFrame:
    """Create sample data - REPLACE THIS with your actual data loading."""
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
                'truth': np.random.choice([0, 1], p=[0.9, 0.1])  # Optional truth column
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
            html.H3("Score Map (0=Blue, 1=Red)", style={'textAlign': 'center'}),
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
    
    # Create maps
    density_path = create_density_map(df_hour, center_lat, center_lng)
    score_path = create_score_map(df_hour, center_lat, center_lng)
    
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
    app.run_server(debug=True, port=8050)
