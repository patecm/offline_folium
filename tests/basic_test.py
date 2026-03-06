import dash
from dash import html
import folium

# 1. Create a Folium map object

m = folium.Map(location=[45.5236, -122.6750], zoom_start=13)
folium.Marker(location=[45.5236, -122.6750], popup="Hello Dash").add_to(m)

# 2. Render the map to an HTML string
# The _repr_html_() method returns a string with the necessary iframe HTML/JS page content
m.save('test_map.html')
map_html = m._repr_html_()

# 3. Integrate with Dash
app = dash.Dash(__name__)

app.layout = html.Div(
    children=[
        html.H1("Folium Map in Dash"),
        html.Iframe(
            # Use srcDoc to pass the HTML string directly
            srcDoc=map_html,
            # Set width and height for proper display
            width="100%",
            height="500px",
            # Add a title for accessibility
            title="Folium Map"
        )
    ]
)

if __name__ == '__main__':
    # Run the app
    app.run(debug=True)
