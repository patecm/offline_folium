"""
Standalone HTML H3 Dashboard Generator
Creates a single HTML file with time slider - no server needed!

Usage:
  python generate_standalone_dashboard.py
  
Then open: h3_dashboard_standalone.html in your browser
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import h3
from pathlib import Path
from datetime import datetime

from offline_folium import OfflineMap
import folium
from branca.colormap import LinearColormap


# ============================================================================
# CONFIGURATION
# ============================================================================
THRESHOLD = 0.5  # Where white appears in score map


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


def create_density_map(df_hour: pd.DataFrame, center_lat: float, center_lng: float, map_id: str) -> str:
    """Create density map and return HTML with custom div ID."""
    m = OfflineMap(
        location=[center_lat, center_lng],
        zoom_start=6,
        tiles="CartoDB positron",
        control_scale=True,
    )
    
    if len(df_hour) > 0:
        vmin = df_hour['density'].min()
        vmax = df_hour['density'].max()
        
        colors = ['#0d0887', '#6400c8', '#b42c8c', '#f07030', '#fce225']
        colormap = LinearColormap(colors=colors, vmin=vmin, vmax=vmax, caption='Density')
        
        for _, row in df_hour.iterrows():
            cell = row['h3_cell']
            density = row['density']
            feature = h3_cell_to_geojson_polygon(cell)
            fill_color = colormap(density)
            
            folium.GeoJson(
                feature,
                style_function=lambda feat, color=fill_color: {
                    "color": "#444444", "weight": 1,
                    "fillColor": color, "fillOpacity": 0.6,
                },
                tooltip=folium.Tooltip(f"H3: {cell}<br>Density: {density:.2f}"),
            ).add_to(m)
        
        colormap.add_to(m)
    
    # Get HTML and replace the default div id
    html = m._repr_html_()
    html = html.replace('id="map_', f'id="{map_id}_')
    return html


def create_score_map(df_hour: pd.DataFrame, center_lat: float, center_lng: float, map_id: str) -> str:
    """Create score map and return HTML with custom div ID."""
    m = OfflineMap(
        location=[center_lat, center_lng],
        zoom_start=6,
        tiles="CartoDB positron",
        control_scale=True,
    )
    
    if len(df_hour) > 0:
        colors = ['#0000ff', '#ffffff', '#ff0000']
        index = [0.0, THRESHOLD, 1.0]
        colormap = LinearColormap(
            colors=colors, index=index, vmin=0.0, vmax=1.0,
            caption=f'Score (white at {THRESHOLD})'
        )
        
        for _, row in df_hour.iterrows():
            cell = row['h3_cell']
            score = row['score']
            feature = h3_cell_to_geojson_polygon(cell)
            fill_color = colormap(score)
            
            folium.GeoJson(
                feature,
                style_function=lambda feat, color=fill_color: {
                    "color": "#444444", "weight": 1,
                    "fillColor": color, "fillOpacity": 0.6,
                },
                tooltip=folium.Tooltip(f"H3: {cell}<br>Score: {score:.3f}"),
            ).add_to(m)
        
        colormap.add_to(m)
    
    # Get HTML and replace the default div id
    html = m._repr_html_()
    html = html.replace('id="map_', f'id="{map_id}_')
    return html


def generate_standalone_dashboard(df: pd.DataFrame, output_file: str = "h3_dashboard_standalone.html"):
    """Generate standalone HTML file with time slider."""
    
    # Get unique hours
    hours = sorted(df['hour'].unique())
    center_lat = 40.0
    center_lng = -100.0
    
    # Generate all map HTMLs
    density_maps = {}
    score_maps = {}
    
    print(f"Generating maps for {len(hours)} time periods...")
    for i, hour in enumerate(hours):
        print(f"  {i+1}/{len(hours)}: {hour}")
        df_hour = df[df['hour'] == hour].copy()
        
        density_maps[i] = create_density_map(df_hour, center_lat, center_lng, f"density_{i}")
        score_maps[i] = create_score_map(df_hour, center_lat, center_lng, f"score_{i}")
    
    # Build HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>H3 Dashboard - Standalone</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .controls {{
            background: white;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .slider-container {{
            margin: 20px 0;
        }}
        .slider {{
            width: 100%;
        }}
        .hour-display {{
            font-size: 18px;
            font-weight: bold;
            text-align: center;
            margin: 10px 0;
        }}
        .maps-container {{
            display: flex;
            gap: 20px;
        }}
        .map-wrapper {{
            flex: 1;
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .map-title {{
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 10px;
            text-align: center;
        }}
        .map-content {{
            position: relative;
        }}
        .map-item {{
            display: none;
        }}
        .map-item.active {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>H3 Dashboard</h1>
        <p>Interactive visualization with {len(hours)} time periods</p>
    </div>
    
    <div class="controls">
        <div class="hour-display" id="hourDisplay">Loading...</div>
        <div class="slider-container">
            <input type="range" min="0" max="{len(hours)-1}" value="0" 
                   class="slider" id="timeSlider" 
                   oninput="updateMaps(this.value)">
        </div>
    </div>
    
    <div class="maps-container">
        <div class="map-wrapper">
            <div class="map-title">Density Map</div>
            <div class="map-content" id="densityMaps">
"""
    
    # Add all density maps
    for i, html_content in density_maps.items():
        active_class = "active" if i == 0 else ""
        html += f'                <div class="map-item {active_class}" data-hour="{i}">\n'
        html += f'                    {html_content}\n'
        html += '                </div>\n'
    
    html += """
            </div>
        </div>
        
        <div class="map-wrapper">
            <div class="map-title">Score Map</div>
            <div class="map-content" id="scoreMaps">
"""
    
    # Add all score maps
    for i, html_content in score_maps.items():
        active_class = "active" if i == 0 else ""
        html += f'                <div class="map-item {active_class}" data-hour="{i}">\n'
        html += f'                    {html_content}\n'
        html += '                </div>\n'
    
    # Add JavaScript and close HTML
    hours_js = str(list(hours))
    html += f"""
            </div>
        </div>
    </div>
    
    <script>
        const hours = {hours_js};
        
        function updateMaps(index) {{
            // Update display
            document.getElementById('hourDisplay').textContent = 
                'Showing data for: ' + hours[index];
            
            // Hide all maps
            document.querySelectorAll('.map-item').forEach(item => {{
                item.classList.remove('active');
            }});
            
            // Show selected maps
            document.querySelectorAll(`.map-item[data-hour="${{index}}"]`).forEach(item => {{
                item.classList.add('active');
            }});
        }}
        
        // Initialize
        updateMaps(0);
    </script>
</body>
</html>
"""
    
    # Save file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✓ Dashboard saved to: {output_file}")
    print(f"  File size: {len(html) / 1024:.1f} KB")
    print(f"  Just open it in your browser - no server needed!")


if __name__ == '__main__':
    # Generate sample data
    print("Generating sample data...")
    hours = pd.date_range('2024-01-01', periods=24, freq='h')
    hours = [h.strftime('%Y-%m-%d_%H') for h in hours]
    
    # Create sample H3 cells (resolution 3 covers ~12,000 km²)
    center_lat, center_lng = 40.0, -100.0
    center_cell = h3.latlng_to_cell(center_lat, center_lng, 3)
    cells = list(h3.grid_disk(center_cell, 2))  # Get surrounding cells
    
    data = []
    for hour in hours:
        for cell in cells:
            data.append({
                'hour': hour,
                'h3_cell': cell,
                'density': np.random.uniform(0, 100),
                'score': np.random.uniform(0, 1),
                'truth': np.random.choice([0, 1], p=[0.9, 0.1])
            })
    
    df = pd.DataFrame(data)
    
    # Replace with your actual data:
    # df = pd.read_csv('your_data.csv')
    
    generate_standalone_dashboard(df)