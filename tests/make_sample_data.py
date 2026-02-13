import pandas as pd
import numpy as np
import h3
from pathlib import Path
from datetime import datetime

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

df = create_sample_data()
breakpoint()
