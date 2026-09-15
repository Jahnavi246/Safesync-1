"""
data.py - Data Operations and Dynamic Shelter Engine for SAFESYNC
"""
import sqlite3
import math

DB_FILE = "safesync_habitation.db"

def init_db():
    """Initializes SQLite database table for storing habitation profiles."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            vulnerability TEXT,
            affected_people INTEGER
        )
    """)
    conn.commit()
    conn.close()

def save_profile_to_db(name, location, vulnerability="Low", affected_people=6):
    """Saves or updates habitation profile data in SQLite database."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_profiles")  # Keeps active profile updated
    cursor.execute("""
        INSERT INTO user_profiles (name, location, vulnerability, affected_people)
        VALUES (?, ?, ?, ?)
    """, (name, location, vulnerability, affected_people))
    conn.commit()
    conn.close()

def load_profile_from_db():
    """Loads the saved profile record from SQLite database."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, location, vulnerability, affected_people FROM user_profiles ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"name": row[0], "location": row[1], "vulnerability": row[2], "affected_people": row[3]}
    return {"name": "Ramesh Kumar", "location": "Guntur Central", "vulnerability": "Low", "affected_people": 6}

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates Haversine distance in kilometers between two geo-coordinates."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def generate_dynamic_shelters(user_lat, user_lon, location_name):
    """
    Dynamically generates and locates local relief shelters around the search location.
    """
    clean_loc = location_name.split(',')[0].strip()
    
    shelter_configs = [
        {"suffix": "Indoor Sports Complex", "lat_off": 0.008, "lon_off": 0.005, "tot": 500, "occ": 120, "ramp": "Yes"},
        {"suffix": "Central Community Hall", "lat_off": -0.012, "lon_off": 0.009, "tot": 200, "occ": 150, "ramp": "Yes"},
        {"suffix": "St. Mary High School", "lat_off": 0.015, "lon_off": -0.011, "tot": 150, "occ": 145, "ramp": "No"},
        {"suffix": "City Emergency Relief Node", "lat_off": -0.005, "lon_off": -0.007, "tot": 300, "occ": 80, "ramp": "Yes"}
    ]

    shelter_list = []
    for s in shelter_configs:
        s_lat = round(user_lat + s["lat_off"], 4)
        s_lon = round(user_lon + s["lon_off"], 4)
        dist = calculate_haversine_distance(user_lat, user_lon, s_lat, s_lon)
        avail = s["tot"] - s["occ"]
        
        shelter_list.append({
            "Shelter Name": f"{clean_loc} {s['suffix']}",
            "Location": f"{clean_loc} Region",
            "lat": s_lat,
            "lon": s_lon,
            "Total Cap": s["tot"],
            "Occupied Cap": s["occ"],
            "Available Cap": avail,
            "Accessibility Ramp": s["ramp"],
            "Distance": f"{dist} km",
            "dist_num": dist
        })

    # Sort shelters in order of proximity
    return sorted(shelter_list, key=lambda item: item["dist_num"])
