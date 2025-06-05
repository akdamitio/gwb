import geopandas as gpd
import folium
import json
import streamlit as st
from folium import Element
from datetime import date
import hashlib




# Load the shapefile
@st.cache_data

def load_data():
    gdf = gpd.read_file("ne_110m_admin_0_countries.shp")
    gdf = gdf.to_crs(epsg=4326)
    return gdf

def safe_unicode(s):
    return s.encode('utf-8', 'replace').decode('utf-8') if isinstance(s, str) else s



# Prepare map
st.set_page_config(layout="wide")
with st.container():
    st.markdown("<h1 style='text-align:center;'>🌍 No Bordle</h1>", unsafe_allow_html=True)
gdf = load_data()

def get_daily_country(gdf):
    # Use today's date to get consistent hash
    today_str = str(date.today())
    hashed = int(hashlib.sha256(today_str.encode()).hexdigest(), 16)
    idx = hashed % len(gdf)
    return gdf.iloc[idx]

selected = get_daily_country(gdf)
selected_name = selected['ADMIN'] if 'ADMIN' in selected else selected['name']
selected_name = safe_unicode(selected_name)

selected_geom = selected.geometry

# Build HTML-compatible map
m = folium.Map(location=[20, 0], zoom_start=3, tiles=None)

# Add Esri tile layer
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Tiles © Esri',
    control=False
).add_to(m)

# Style banner + cursor
css = f"""
<style>
    .leaflet-container {{
        cursor: crosshair !important;
    }}
    #guessBanner {{
        position: fixed;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0,0,0,0.75);
        color: white;
        padding: 10px 20px;
        font-size: 1.2em;
        font-family: sans-serif;
        border-radius: 8px;
        z-index: 9999;
        pointer-events: none;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        height: 50px;              /* 👈 Fixed height */
        display: flex;             /* 👈 Center vertically */
        align-items: center;
        justify-content: center;
        white-space: nowrap;       /* 👈 Prevent line breaks */
        overflow: hidden;
    }}
</style>
<div id='guessBanner'>🎯 Find: <strong>{selected_name}</strong></div>
"""
m.get_root().html.add_child(Element(css))

# GeoJSON geometry
geojson_geom = json.loads(gpd.GeoSeries([selected_geom]).to_json())['features'][0]['geometry']
geojson_str = json.dumps(geojson_geom)

# JS logic
map_var = m.get_name()
turf_js = f"""
(function() {{
    var gameOver = false;
    var turfScript = document.createElement('script');
    turfScript.src = 'https://cdn.jsdelivr.net/npm/@turf/turf@6/turf.min.js';
    turfScript.onload = function() {{
        var countryGeoJSON = {geojson_str};
        var guessCount = 0;
        const updateBanner = (text) => {{
            document.getElementById('guessBanner').innerText = text;
        }};

        var countryLayer = null;

        {map_var}.whenReady(function() {{
        
            // LocalStorage key

            const playedKey = "hasGuessed_" + new Date().toISOString().slice(0,10);

            let locked = false;
            const played = localStorage.getItem(playedKey);
            const savedScore = localStorage.getItem(playedKey + "_score");
            
            var guessCount = Number(localStorage.getItem(playedKey + "_guesses"));

            if (played && savedScore) {{
                updateBanner("✅ You already played today. | Guesses: " + savedScore);
                locked = true;
                gameOver = true;

                // Optionally re-show the country
                countryLayer = L.geoJSON(countryGeoJSON, {{
                    style: {{ color: 'green', weight: 3, fillOpacity: 0.3 }}
                }}).addTo({map_var});
            }}

            {map_var}.on('click', function(e) {{
                if(gameOver === false){{
                    guessCount += 1;
                    localStorage.setItem(playedKey + "_guesses", guessCount);
                }}
                var pt = turf.point([e.latlng.lng, e.latlng.lat]);
                let shape;

                if (countryGeoJSON.type === "Polygon") {{
                    shape = turf.polygon(countryGeoJSON.coordinates);
                }} else if (countryGeoJSON.type === "MultiPolygon") {{
                    shape = turf.multiPolygon(countryGeoJSON.coordinates);
                }} else {{
                    console.warn("Unsupported geometry type:", countryGeoJSON.type);
                }}

                let inside = shape ? turf.booleanPointInPolygon(pt, shape) : false;

                if (inside) {{
                    gameOver = true;
                    localStorage.setItem(playedKey, "true");
                    localStorage.setItem(playedKey + "_score", guessCount);
                    locked = true;
                    updateBanner("You cheated | Guesses: " + guessCount);
                    if (!countryLayer) {{
                        countryLayer = L.geoJSON(countryGeoJSON, {{
                            style: {{color: 'green', weight: 3, fillOpacity: 0.3}}
                        }}).addTo({map_var});
                    }}
                }} else {{
                    if(gameOver === false){{
                        updateBanner("Find: {selected_name} | Ha bad | Guesses: " + guessCount);
                    }}
                }}
            }});
        }});
    }};
    document.head.appendChild(turfScript);
}})();
"""
m.get_root().script.add_child(Element(turf_js))

# Render in Streamlit
from streamlit.components.v1 import html as st_html
html_string = m.get_root().render()
html_string = html_string.encode('utf-8', 'replace').decode('utf-8')
#st_html(html_string, height=700, scrolling=True)
st_html(m.get_root().render(), height=700, scrolling=False)


