import math
from geopy.geocoders import Nominatim

def get_coordinates(location_name):
    """Geocodes location names into real-time coordinates."""
    try:
        geolocator = Nominatim(user_agent="safesync_disaster_app")
        loc = geolocator.geocode(location_name)
        if loc:
            return loc.latitude, loc.longitude
    except Exception:
        pass
    return 16.3067, 80.4365  # Fallback to default Guntur Central coordinates

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def evaluate_safesync(hazard_type, severity, user_profile, shelters, user_lat=16.3067, user_lon=80.4365):
    severity_weights = {"Low": 25, "Medium": 50, "High": 75, "Critical": 100}
    sev_score = severity_weights.get(severity, 50)
    
    v_score = 0
    if user_profile['elderly'] > 0: v_score += 25
    if user_profile['children'] > 0: v_score += 20
    if user_profile['disabilities'] > 0: v_score += 30
    if user_profile['mobility'] != 'Normal': v_score += 25
    
    vulnerability_level = "Low"
    if v_score >= 60: vulnerability_level = "High"
    elif v_score >= 30: vulnerability_level = "Medium"
    
    risk_score = min(100, int((sev_score * 0.6) + (v_score * 0.4)))
    
    if risk_score >= 75:
        risk_zone = "Red Zone"
        zone_color = "red"
    elif risk_score >= 55:
        risk_zone = "Orange Zone"
        zone_color = "orange"
    elif risk_score >= 35:
        risk_zone = "Yellow Zone"
        zone_color = "yellow"
    else:
        risk_zone = "Green Zone"
        zone_color = "green"
        
    if risk_score >= 70 or (severity == "Critical" and vulnerability_level != "Low"):
        priority = "Immediate Relocation"
        priority_color = "red"
    elif risk_score >= 50:
        priority = "High Priority"
        priority_color = "orange"
    elif risk_score >= 30:
        priority = "Medium Priority"
        priority_color = "yellow"
    else:
        priority = "Low Priority"
        priority_color = "green"
        
    req_cap = user_profile['num_people']
    best_shelter = None
    min_dist = float('inf')
    
    processed_shelters = []
    for s in shelters:
        dist = calculate_distance(user_lat, user_lon, s['lat'], s['lon'])
        s['distance_km'] = dist
        
        if s['available_capacity'] >= req_cap:
            s['status'] = "Capacity Available"
        elif s['available_capacity'] > 0:
            s['status'] = "Capacity Limited"
        else:
            s['status'] = "Shelter Full"
            
        is_suitable = s['available_capacity'] >= req_cap
        if user_profile['mobility'] != 'Normal' and not s['has_ramp']:
            is_suitable = False
            
        s['suitable'] = is_suitable
        if is_suitable and dist < min_dist:
            min_dist = dist
            best_shelter = s
            
        processed_shelters.append(s)
        
    if not best_shelter and processed_shelters:
        best_shelter = sorted(processed_shelters, key=lambda x: x['distance_km'])[0]

    return {
        "risk_score": risk_score,
        "risk_zone": risk_zone,
        "zone_color": zone_color,
        "vulnerability_level": vulnerability_level,
        "relocation_priority": priority,
        "priority_color": priority_color,
        "recommended_shelter": best_shelter,
        "all_shelters": processed_shelters
    }
