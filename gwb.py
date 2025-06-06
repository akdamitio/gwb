import geopandas as gpd
import folium
import json
import streamlit as st
from folium import Element
from datetime import date
import hashlib
import random

phrases = ['🙈', "i'm working on a beginner mode,\nyou might enjoy that one",'ha bad', "didn't hurt yourself thinking that hard, right?", 'cmon dawg', 'just blow in from stupid town?', 'double dose of stupid pills this morning?', 'oh so close! or are you...?', "where'd you go to school, idiot university?", 'srsly?', 'lol', "ain't it chief", 'this is painful', 'tough scenes', '...', 'nah bro', 'oof', "you were mama's 'special little boy' huh?", "there's always tomorrow", 'ur doing great sweetie', "you are dumb", 'no', 'ok this time try for real', 'do you have special needs?', 'nuh uh', "shame what happened to amelia earhardt...\nshould've been you", "don't reproduce", 'you have the IQ of butter lettuce', '🤨']
shuf = random.sample(phrases, k=6)
js_messages = json.dumps(shuf)


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
    .star-marker {{
        color: gold;
        font-size: 20px;
        line-height: 20px;
        text-align: center;
        pointer-events: none;
    }}
    .star-marker::before {{
        content: "★";        
    }}

    .plus-marker {{
      width: 40px;
      height: 40px;
      display: flex;
      justify-content: center;
      align-items: center;
      pointer-events: none;
      font-weight: 200
    }}



    #lockButton {{
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9999;
        padding: 10px 20px;
        background: #007BFF;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 1em;
        font-weight: bold;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        cursor: pointer;
    }}
    #lockButton:disabled {{
        background: #888;
        cursor: not-allowed;
    }}

    #wrongGuessPopup {{
        position: fixed;
        top: 60px; /* Slightly below the #guessBanner which is at 10px + ~40px height */
        left: 50%;
        transform: translateX(-50%);
        background: rgba(255, 0, 0, 0.9);
        color: white;
        padding: 8px 16px;
        font-size: 1em;
        font-family: sans-serif;
        border-radius: 6px;
        z-index: 9999;
        opacity: 0;
        transition: opacity 0.5s ease-in-out;
        pointer-events: none;
        white-space: nowrap;
    }}
        
</style>
<div id='guessBanner'>🎯 Find:  <strong>{selected_name}</strong></div>
<div><button id="lockButton">🔒 Lock In Guess</button></div>
<div id="wrongGuessPopup"></div>

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
        const lockBtn = document.getElementById("lockButton");
        var pt = 0
        const wrongGuessMessages = {js_messages};

        const saveGuess = (lat, lng) => {{
            const stored = JSON.parse(localStorage.getItem('guesses') || '[]');
            stored.push([lat, lng]);
            localStorage.setItem('guesses', JSON.stringify(stored));
        }};

        const showWrongGuessPopup = (message) => {{
            const popup = document.getElementById('wrongGuessPopup');
            if (!popup) return;
            popup.innerText = message;
            popup.style.opacity = 0.7;
            setTimeout(() => {{
                popup.style.opacity = 0;
            }}, 3000);
        }};

        const markers = document.getElementsByClassName("plus-marker");


        const updateBanner = (text) => {{
            document.getElementById('guessBanner').innerText = text;
        }};

        var countryLayer = null;

        {map_var}.whenReady(function() {{

        const plusIcon = L.divIcon({{
          className: '',
          html: `
            <div class="plus-marker">
              <svg width="20" height="20" viewBox="0 0 20 20">
                <line x1="10" y1="4" x2="10" y2="16" stroke="red" stroke-width="2"/>
                <line x1="4" y1="10" x2="16" y2="10" stroke="red" stroke-width="2"/>
              </svg>
            </div>
          `,
          iconSize: [40, 40],
          iconAnchor: [20, 20]
        }});        


        
            // LocalStorage key

            const playedKey = "hasGuessed_" + new Date().toISOString().slice(0,10);

            let locked = false;
            const played = localStorage.getItem(playedKey);
            var tapCount = 0;
            const savedScore = localStorage.getItem(playedKey + "_score");
            
            guessCount = Number(localStorage.getItem(playedKey + "_guesses"));

            if (savedScore === "Suck") {{
                updateBanner("✅ You already played today. | Guesses: " + savedScore);
                locked = true;
                gameOver = true;
                // Optionally re-show the country
                countryLayer = L.geoJSON(countryGeoJSON, {{
                    style: {{ color: 'red', weight: 3, fillOpacity: 0.3 }}
                }}).addTo({map_var});

            }}

            if (played) {{
                updateBanner("✅ You already played today. | Guesses: " + savedScore);
                locked = true;
                gameOver = true;

                // Optionally re-show the country
                countryLayer = L.geoJSON(countryGeoJSON, {{
                    style: {{ color: 'green', weight: 3, fillOpacity: 0.3 }}
                }}).addTo({map_var});
            }}


            const reloadGuesses = () => {{
                const stored = JSON.parse(localStorage.getItem('guesses') || '[]');
                for (const [lat, lng] of stored) {{
                    L.circleMarker([lat, lng], {{
                        radius: 3,
                        color: 'red',
                        weight: 1,
                        fillColor: 'red',
                        fillOpacity: 0.6,
                        className: 'guess-dot'
                    }}).addTo({map_var});
                }}
            }};
            reloadGuesses();

            {map_var}.on('click', function(e) {{
                if(gameOver === false){{
                    tapCount = 1;
                    pt = turf.point([e.latlng.lng, e.latlng.lat]);

                    while (markers.length > 0) {{
                        markers[0].remove();
                    }}

                    L.marker(e.latlng, {{
                        icon: L.divIcon({{
                            className: 'plus-marker',
                            iconSize: [40, 40],
                            iconAnchor: [12, 26]
                        }})
                    }}).addTo({map_var});                    
                }}
            }});

            lockButton.addEventListener("click", function() {{
                if(tapCount === 1) {{
                    guessCount += 1
                    localStorage.setItem(playedKey + "_guesses", guessCount);
                    saveGuess(pt.geometry.coordinates[1], pt.geometry.coordinates[0]);

                    tapCount = 0

                    while (markers.length > 0) {{
                        markers[0].remove();
                    }}
                    

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
                        updateBanner("Bingo | Guesses: " + guessCount);
                        if (!countryLayer) {{
                            countryLayer = L.geoJSON(countryGeoJSON, {{
                                style: {{color: 'green', weight: 3, fillOpacity: 0.3}}
                            }}).addTo({map_var});
                        }}

                        L.marker([pt.geometry.coordinates[1], pt.geometry.coordinates[0]], {{
                            icon: L.divIcon({{
                                className: 'star-marker',
                                iconSize: [20, 20],
                                iconAnchor: [10,10]

                            }})
                        }}).addTo({map_var});


                    }} else {{
                        if(gameOver === false){{
                        
                            // Add marker at clicked location
                            L.circleMarker([pt.geometry.coordinates[1], pt.geometry.coordinates[0]], {{
                                radius: 3,
                                color: 'red',
                                fillColor: 'red',
                                Opacity: 0.8
                            }}).addTo({map_var});       

                            const messageIndex = guessCount - 1;
                            const msg = wrongGuessMessages[messageIndex % wrongGuessMessages.length];
                            showWrongGuessPopup(msg);   
                            
                            if (guessCount === 6) {{
                                countryLayer = L.geoJSON(countryGeoJSON, {{
                                    style: {{ color: 'red', weight: 3, fillOpacity: 0.3 }}
                                }}).addTo({map_var});
                                updateBanner("6 tries is enough. You lose.");
                                gameOver = true;
                                locked = true;
                                localStorage.setItem(playedKey + "_score", "Suck")


                            }} else{{
                                updateBanner("Find: {selected_name} | Guesses: " + guessCount);
                            
                            }}

                        }}
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
st_html(m.get_root().render(), height=450, scrolling=False)


