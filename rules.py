"""
rules.py - Risk Evaluation & Emergency Protocol Rules Engine for SAFESYNC
"""

def evaluate_risk_score(hazard_type, telemetry, vulnerability_level="Low"):
    """
    Calculates dynamic overall risk score (0 - 100) based on live telemetry & hazard conditions.
    """
    rain = telemetry.get("rain_mm", 0.0)
    wind = telemetry.get("wind_speed", 0.0)
    alert = telemetry.get("imd_alert", "GREEN")

    # Dynamic base score calculated from weather telemetry thresholds
    if alert == "RED" or rain > 100 or wind > 75:
        base_score = 80
    elif alert == "ORANGE" or rain > 50 or wind > 45:
        base_score = 55
    elif alert == "YELLOW" or rain > 15 or wind > 25:
        base_score = 35
    else:
        base_score = 15  # Normal clear conditions baseline

    # Adjustment based on Habitation Vulnerability Level
    if vulnerability_level == "High":
        base_score += 10
    elif vulnerability_level == "Medium":
        base_score += 5

    return min(base_score, 100)


def determine_relocation_priority(risk_score):
    """
    Determines relocation priority status, risk zone designation, and badge color based on risk score.
    """
    if risk_score >= 75:
        return "Immediate Relocation", "Red Zone", "#ff4b4b"
    elif risk_score >= 50:
        return "High Priority", "Orange Zone", "#ffa500"
    elif risk_score >= 30:
        return "Medium Priority", "Yellow Zone", "#e6b800"
    else:
        return "Low Risk / Monitor", "Green Zone", "#28a745"


def get_emergency_action_plan(hazard_type, risk_score=15):
    """
    Returns step-by-step emergency action plans tailored to specific hazards and current risk severity.
    """
    if risk_score < 30:
        return [
            "1. Monitor local weather channels for routine updates.",
            "2. Ensure household emergency contact lists are up to date.",
            "3. Inspect drainage and emergency access points around habitation.",
            "4. Keep a standard first-aid kit stocked and accessible."
        ]

    action_plans = {
        "Flood 🌊": [
            "1. Move immediately to higher ground or upper floors.",
            "2. Switch off main power supply and gas connections.",
            "3. Do not walk, swim, or drive through moving floodwaters.",
            "4. Evacuate to designated community flood relief shelter."
        ],
        "Cyclone 🌀": [
            "1. Remain indoors away from doors and glass windows.",
            "2. Keep emergency supplies and battery-operated radios ready.",
            "3. Beware of the calm 'eye' of the storm; wait for official clearance.",
            "4. Relocate to cyclone shelters if residing in vulnerable structures."
        ],
        "Earthquake 🫨": [
            "1. Drop, Cover, and Hold On under sturdy furniture.",
            "2. Stay clear of glass windows, exterior walls, and heavy fixtures.",
            "3. Move to open areas away from buildings and overhead power lines if outdoors.",
            "4. Do not use elevators during post-shock evacuation."
        ],
        "Fire Emergency 🔥": [
            "1. Evacuate immediately using designated emergency stairwells.",
            "2. Crawl low under smoke to avoid toxic gas inhalation.",
            "3. Feel door handles with the back of your hand before opening.",
            "4. Call fire emergency services (101) once in a safe zone."
        ],
        "Landslide ⛰️": [
            "1. Evacuate slope-adjacent homes immediately upon hearing rumbling noises.",
            "2. Avoid valley floors and direct stream channels.",
            "3. Protect your head and curl into a tight ball if escape is impossible.",
            "4. Report utility line breaks to local emergency authorities."
        ],
        "Severe Thunderstorm 🌩️": [
            "1. Seek shelter inside a sturdy building or hard-topped vehicle.",
            "2. Unplug electrical appliances and avoid wired electronics.",
            "3. Avoid isolated trees, metal fences, and open high fields.",
            "4. Wait 30 minutes after the last thunderclap before stepping outside."
        ],
        "Tsunami 🌊": [
            "1. Move inland to high ground immediately following strong coastal shaking.",
            "2. Avoid going near the shore to observe receding sea waters.",
            "3. Tune into coastal emergency broadcast frequencies.",
            "4. Stay on high ground until official tsunami warnings are canceled."
        ],
        "Chemical Leak ⚠️": [
            "1. Cover nose and mouth with a wet cloth or respirator.",
            "2. Move crosswind or upwind away from the hazardous source.",
            "3. Seal doors and windows if sheltering in place.",
            "4. Decontaminate by washing exposed skin and changing clothes."
        ],
        "Heatwave ☀️": [
            "1. Hydrate regularly with water and oral rehydration solutions (ORS).",
            "2. Avoid direct sunlight exposure between 11:00 AM and 4:00 PM.",
            "3. Wear light, loose-fitting cotton clothing.",
            "4. Move vulnerable individuals to cooled or shaded spaces."
        ]
    }
    return action_plans.get(
        hazard_type,
        ["1. Monitor weather updates.", "2. Keep emergency kit ready.", "3. Follow local authority guidance."]
    )
