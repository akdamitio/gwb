import geopandas as gpd
import folium
import json
import streamlit as st
from branca.element import Element
from datetime import date
import hashlib
import random
from streamlit_javascript import st_javascript
import time

mode = 'impossible'

st.set_page_config(layout="wide")



js_code = "new Date().toISOString().split('T')[0]"  # e.g., "2025-06-08"
date_string = st_javascript(js_code=js_code)



phrases = ['🙈', "i'm working on a beginner mode,\nyou might enjoy that one",'ha bad', "didn't hurt yourself thinking that hard, right?", 'cmon dawg', 'just blow in from stupid town?', 'double dose of stupid pills this morning?', 'oh so close! or are you...?', "where'd you go to school, idiot university?", 'srsly?', 'lol', "ain't it chief", 'this is painful', 'tough scenes', '...', 'nah bro', 'oof', "you were mama's 'special little boy' huh?", "there's always tomorrow", 'ur doing great sweetie', "you are dumb", 'no', 'ok this time try for real', 'nuh uh', "shame what happened to amelia earhart...\nshould've been you", "don't reproduce", 'you have the IQ of butter lettuce', '🤨']
shuf = random.sample(phrases, k=6)
js_messages = json.dumps(shuf)


# Load the shapefile
@st.cache_data

def load_data():
    gdf = gpd.read_file("ne_10m_admin_0_countries.shp")
    gdf = gdf.to_crs(epsg=4326)
    return gdf

def safe_unicode(s):
    return s.encode('utf-8', 'replace').decode('utf-8') if isinstance(s, str) else s



with st.container():
    st.markdown("<h1 style='text-align:center;'>🌍 ImpossiBordle</h1>", unsafe_allow_html=True)
gdf = load_data()

def get_daily_country(gdf):
    # Use today's date to get consistent hash
    today_str = f"{date_string}-{mode}"
    time.sleep(2)
    hashed = int(hashlib.sha256(today_str.encode()).hexdigest(), 16)
    idx = hashed % len(gdf)
    return gdf.iloc[idx]

selected = get_daily_country(gdf)
selected_name = selected['ADMIN'] if 'ADMIN' in selected else selected['name']
selected_type = selected['TYPE']
selected_sov = ''

if(selected['SOVEREIGNT'] != selected_name):
    selected_sov = f" ({selected['SOVEREIGNT']})"
    selected_sov = safe_unicode(selected_sov)
    
selected_name = safe_unicode(selected_name)

selected_geom = selected.geometry

# Build HTML-compatible map
m = folium.Map(
    location=[20, 0],
    zoom_start=0.4,
    tiles=None,
    zoom_control=True,
    prefer_canvas=True
)



smooth_zoom_js = """
<script>
    var originalInit = L.Map.prototype.initialize;
    L.Map.prototype.initialize = function (id, options) {
        options.zoomSnap = 0;     // allow fractional zoom
        options.zoomDelta = 0.1;  // small zoom steps for smooth experience
        return originalInit.call(this, id, options);
    };
</script>
"""

m.get_root().html.add_child(Element(smooth_zoom_js))



b = r"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

# Equator: Line from -180 to +180 longitude at 0 latitude
folium.PolyLine(
    locations=[[0, -180], [0, 180]],
    color='red',
    weight=1.2,
    opacity=0.6
).add_to(m)



for a in [-90, -60, -30, 30, 60, 90]:
    folium.PolyLine(
        locations=[[a, -180], [a, 180]],
        color='black',
        weight=0.5,
        opacity=1
    ).add_to(m)

# Prime Meridian: Line from -90 to +90 latitude at 0 longitude
folium.PolyLine(
    locations=[[-90, 0], [90, 0]],
    color='red',
    weight=1.2,
    opacity=1
).add_to(m)

for a in [-180, -150, -120, -90, -60, -30, 30, 60, 90, 120, 150, 180]:
    folium.PolyLine(
        locations=[[-90, a], [90, a]],
        color='black',
        weight=0.5,
        opacity=1
    ).add_to(m)

# Style banner + cursor
css = f"""
<style>
    .leaflet-container {{
        cursor: crosshair !important;
        z-index: 9998
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
        /*height: 50px; */             /* 👈 Fixed height */
        display: flex;             /* 👈 Center vertically */
        align-items: center;
        justify-content: center;
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
        content: "✦";        
    }}

    .x-marker {{
        color: red;
        font-size: 30px;
        line-height: 30px;
        text-align: center;
        pointer-events: none;
        cursor: crosshair !important;

    }}
    .x-marker::before {{
        content: "×";        
    }}    

    .plus-marker {{
      width: 40px;
      height: 40px;
      display: flex;
      justify-content: center;
      align-items: center;
      pointer-events: none;
      font-weight: 200;
      cursor: crosshair;
    }}

    .arrow-marker {{
    color: red
    font-size: 20px;
    line-height: 20px;
    text-align: center;
    pointer-events: none;
    }}
    .arrow-marker::before {{
        content: "➤";        
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

    #map-mask {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        background: black;
        z-index: 1000;
        mask-image: none;
        cursor: crosshair !important;
        -webkit-mask-image: none;
    }}

        
</style>


<div id='guessBanner'>🎯 \u0020 <strong>{selected_name}{selected_sov}</strong></div>
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
    localStorage.clear()


    const today = new Date().toISOString().split('T')[0];  // "2025-06-08"
    const storedDate = localStorage.getItem("lastPlayedDate");
    
    if (storedDate !== today) {{
        localStorage.clear();  // or just remove specific keys if needed
        localStorage.setItem("lastPlayedDate", today);
    }}
    
    var turfScript = document.createElement('script');
    turfScript.src = 'https://cdn.jsdelivr.net/npm/@turf/turf@6/turf.min.js';
    turfScript.onload = function() {{
        var countryGeoJSON = {geojson_str};
        var guessCount = 0;
        const lockBtn = document.getElementById("lockButton");
        var pt = 0
        const wrongGuessMessages = {js_messages};

        let border;
        border = turf.polygonToLine(countryGeoJSON);

        var totalDistance = 0;
        function showLosePopup() {{
            const popup = document.createElement('div');
            popup.innerText = `💩 You stink! Average proximity: ${{(totalDistance/6).toFixed(0)}} miles from the border.`;;
            popup.style.position = 'fixed';
            popup.style.top = '70px';
            popup.style.left = '50%';
            popup.style.transform = 'translateX(-50%)';
            popup.style.background = 'rgba(0,0,0,0.85)';
            popup.style.color = 'white';
            popup.style.padding = '12px 20px';
            popup.style.borderRadius = '10px';
            popup.style.fontSize = '1em';
            popup.style.zIndex = '9999';
            popup.style.boxShadow = '0 0 10px rgba(0,0,0,0.5)';
            document.body.appendChild(popup);
        }}
        

        //MASKING \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
        let maskLayer;
        let holes = [];
        let holeId = 0;

        // Initialize the map
        function initMap() {{
            
            // Add base tile layer
            L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',{{attribution: 'Tiles © Esri', detectRetina: true}}).addTo({map_var})        

            
            // Create initial mask
            createMask();
            
            // Update mask when map moves or zooms
            {map_var}.on('zoomend moveend', updateMask);
        }}

        // Create the mask layer
        function createMask() {{
            maskLayer = L.layerGroup().addTo({map_var});
            updateMask();
        }}

        // Update the mask based on current map view and holes
        function updateMask() {{
            // Clear existing mask
            maskLayer.clearLayers();
            
            // Get map bounds
            const bounds = {map_var}.getBounds();
            const ne = bounds.getNorthEast();
            const sw = bounds.getSouthWest();
            
            // Create a large rectangle covering the entire view
            const outerRing = [
                [ne.lat + 1, ne.lng + 1],
                [ne.lat + 1, sw.lng - 1],
                [sw.lat - 1, sw.lng - 1],
                [sw.lat - 1, ne.lng + 1],
                [ne.lat + 1, ne.lng + 1]
            ];
            
            // Create holes (inner rings) for each specified location
            const innerRings = holes.map(hole => {{
                return createCircleCoordinates(hole.lat, hole.lng, hole.radius);
            }});
            
            // Create polygon with holes
            const maskPolygon = L.polygon([outerRing, ...innerRings], {{
                color: 'transparent',
                fillColor: '#808080',
                fillOpacity: 1,
                weight: 0
                cursor: crosshair
            }});
            
            maskLayer.addLayer(maskPolygon);
        }}

        // Create circle coordinates for a given center and radius
        function createCircleCoordinates(lat, lng, radiusKm) {{
            const points = [];
            const steps = 128; // Number of points to approximate circle
            
            for (let i = 0; i < steps; i++) {{
                const angle = (i / steps) * 2 * Math.PI;
                const point = getPointAtDistance(lat, lng, radiusKm, angle);
                points.push([point.lat, point.lng]);
            }}
            
            // Close the circle
            points.push(points[0]);
            
            return points;
        }}

        // Calculate a point at a given distance and bearing from a center point
        function getPointAtDistance(lat, lng, distanceKm, bearing) {{
            const R = 6371; // Earth's radius in km
            const d = distanceKm / R; // Distance in radians
            
            const lat1 = lat * Math.PI / 180;
            const lng1 = lng * Math.PI / 180;
            
            const lat2 = Math.asin(Math.sin(lat1) * Math.cos(d) + 
                                  Math.cos(lat1) * Math.sin(d) * Math.cos(bearing));
            
            const lng2 = lng1 + Math.atan2(Math.sin(bearing) * Math.sin(d) * Math.cos(lat1),
                                          Math.cos(d) - Math.sin(lat1) * Math.sin(lat2));
            
            return {{
                lat: lat2 * 180 / Math.PI,
                lng: lng2 * 180 / Math.PI
            }};
        }}

        // Add a new hole to the mask
        function addHole(pt, radius) {{
            const lat = pt.geometry.coordinates[1];
            const lng = pt.geometry.coordinates[0];
           
            
            const hole = {{
                id: holeId++,
                lat: lat,
                lng: lng,
                radius: radius
            }};
            
            holes.push(hole);

            updateMask();


        }};

        ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



        const saveGuess = (lat, lng) => {{
            const stored = JSON.parse(localStorage.getItem('guesses') || '[]');
            stored.push([lat, lng]);
            localStorage.setItem('guesses', JSON.stringify(stored));
        }};

        const showWrongGuessPopup = (message) => {{
            const popup = document.getElementById('wrongGuessPopup');
            if (!popup) return;
            popup.innerText = message;
            popup.style.opacity = 0.8;
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

        initMap();

            const plusIcon = L.divIcon({{
                className: '',
                html: `
                    <div class="plus-marker">
                        <svg width="40" height="40" viewBox="0 0 40 40">
                            <line x1="20" y1="8" x2="20" y2="32" stroke="red" stroke-width="2"/>
                            <line x1="8" y1="20" x2="32" y2="20" stroke="red" stroke-width="2"/>
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

                totalDistance = Number(localStorage.getItem(playedKey + "_totalDistance"));
        
                
                updateBanner("✅ You already played today. | Guesses: " + savedScore);
                locked = true;
                gameOver = true;
                
                showLosePopup();

                // Optionally re-show the country
                countryLayer = L.geoJSON(countryGeoJSON, {{
                    style: {{ color: 'red', weight: 3, fillOpacity: 0.3 }}
                }}).addTo({map_var});


            }}




            const reloadGuesses = () => {{
                const stored = JSON.parse(localStorage.getItem('guesses') || '[]');
                for (const [lat, lng] of stored) {{
                    L.marker([pt.geometry.coordinates[1], pt.geometry.coordinates[0]], {{
                        icon: L.divIcon({{
                            className: 'x-marker',
                            iconSize: [30, 30],
                            iconAnchor: [15,15]

                        }})
                    }}).addTo({map_var});
                }}
            }};
            reloadGuesses();


            if (played) {{
                updateBanner("✅ You already played today. | Guesses: " + savedScore);
                locked = true;
                gameOver = true;

                const stored = JSON.parse(localStorage.getItem('guesses') || '[]');

                console.log(stored[stored.length - 1][0], stored[stored.length - 1][1]);
                L.marker([stored[stored.length - 1][0], stored[stored.length - 1][1]], {{
                    icon: L.divIcon({{
                        className: 'star-marker',
                        iconSize: [20, 20],
                        iconAnchor: [10,10]

                    }})
                }}).addTo({map_var});

                // Optionally re-show the country
                countryLayer = L.geoJSON(countryGeoJSON, {{
                    style: {{ color: 'green', weight: 3, fillOpacity: 0.3 }}
                }}).addTo({map_var});
            }}

            {map_var}.on('click', function(e) {{
                if(gameOver === false){{

                    if (Math.abs(e.latlng.lng) < 180) {{
                    
                        tapCount = 1;
                        pt = turf.point([e.latlng.lng, e.latlng.lat]);
                        
                        while (markers.length > 0) {{
                            markers[0].remove();
                        }}
                        
                        L.marker([e.latlng.lat, e.latlng.lng], {{ icon: plusIcon }}).addTo({map_var});                   




                    }}
                }}
            }});

            lockButton.addEventListener("click", function() {{
                let distanceToBorder = Infinity

                if(tapCount === 1) {{
                    guessCount += 1
                    localStorage.setItem(playedKey + "_guesses", guessCount);
                    saveGuess(pt.geometry.coordinates[1], pt.geometry.coordinates[0]);

                    if (border.type === "FeatureCollection") {{
                        console.log("a");
                        border.features.forEach(f => {{
                            const dist = turf.pointToLineDistance(pt, f, {{ units: "miles" }});
                            if (dist < distanceToBorder) {{
                                distanceToBorder = dist;
                            }}
                        }});
                        console.log(distanceToBorder);
                    }}else{{

                        if (border.geometry.type === "MultiLineString") {{
                            console.log("b");


                            border.geometry.coordinates.forEach(g => {{
                                console.log(g);
                                const dist = turf.pointToLineDistance(pt, g, {{ units: "miles" }});
                                if (dist < distanceToBorder) {{
                                    distanceToBorder = dist;
                                }}
                            }});
                        }} else{{
                            console.log("c");

                            distanceToBorder = turf.pointToLineDistance(pt, border, {{units: 'miles'}});
                        }}
                    }};
                    console.log(distanceToBorder);

                    totalDistance = totalDistance + distanceToBorder
                    localStorage.setItem(playedKey + "_totalDistance", totalDistance)


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
                        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',{{attribution: 'Tiles © Esri', detectRetina: true}}).addTo({map_var})        

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

            
                            //reveal circle of basemap here
                            
                            let radius = 0;
                            radius  = (guessCount - 1) * 200;
                            addHole(pt, radius);    
                            
                            // Add marker at clicked location
                            L.marker([pt.geometry.coordinates[1], pt.geometry.coordinates[0]], {{
                                icon: L.divIcon({{
                                    className: 'x-marker',
                                    iconSize: [30, 30],
                                    iconAnchor: [15,15]
        
                                }})
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
                                L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',{{attribution: 'Tiles © Esri', detectRetina: true}}).addTo({map_var})        
                                showLosePopup();



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


