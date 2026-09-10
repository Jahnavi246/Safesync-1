import sqlite3

DB_NAME = "hazard_system.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # User Profile Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    name TEXT,
                    age INTEGER,
                    num_people INTEGER,
                    children INTEGER,
                    elderly INTEGER,
                    disabilities INTEGER,
                    mobility TEXT,
                    language TEXT,
                    location TEXT)''')
    
    # Shelters Table
    c.execute('''CREATE TABLE IF NOT EXISTS shelters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    location TEXT,
                    lat REAL,
                    lon REAL,
                    total_capacity INTEGER,
                    occupied_capacity INTEGER,
                    resources TEXT,
                    has_ramp INTEGER)''')
    
    conn.commit()
    
    # Insert Demo Shelters if empty
    c.execute("SELECT COUNT(*) FROM shelters")
    if c.fetchone()[0] == 0:
        demo_shelters = [
            ("Central Community Hall", "Guntur North", 16.3150, 80.4420, 200, 150, "Food, Water, Medical, Ramps", 1),
            ("St. Mary High School", "Guntur West", 16.2980, 80.4210, 150, 145, "Food, Basic First Aid", 0),
            ("Indoor Sports Complex", "Guntur East", 16.3200, 80.4500, 500, 120, "Food, Water, Power Backup, Beds", 1),
            ("City Emergency Shelter", "Guntur Central", 16.3067, 80.4365, 300, 80, "Food, Medical, Ramps", 1)
        ]
        c.executemany('''INSERT INTO shelters (name, location, lat, lon, total_capacity, occupied_capacity, resources, has_ramp)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', demo_shelters)
        conn.commit()

    # Insert Demo User if empty
    c.execute("SELECT COUNT(*) FROM users WHERE username='ramesh'")
    if c.fetchone()[0] == 0:
        c.execute('''INSERT INTO users VALUES ('ramesh', 'pass123', 'Ramesh Kumar', 70, 6, 1, 2, 1, 'Limited Mobility', 'Telugu', 'Guntur Central')''')
        conn.commit()
        
    conn.close()

def get_all_shelters():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, location, lat, lon, total_capacity, occupied_capacity, resources, has_ramp FROM shelters")
    rows = c.fetchall()
    conn.close()
    
    shelters = []
    for r in rows:
        shelters.append({
            "id": r[0], "name": r[1], "location": r[2], "lat": r[3], "lon": r[4],
            "total_capacity": r[5], "occupied_capacity": r[6],
            "available_capacity": r[5] - r[6], "resources": r[7], "has_ramp": bool(r[8])
        })
    return shelters

def get_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name, age, num_people, children, elderly, disabilities, mobility, language, location FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "name": row[0], "age": row[1], "num_people": row[2],
            "children": row[3], "elderly": row[4], "disabilities": row[5],
            "mobility": row[6], "language": row[7], "location": row[8]
        }
    return None

def save_or_update_user(username, data):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO users (username, name, age, num_people, children, elderly, disabilities, mobility, language, location)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
              (username, data['name'], data.get('age', 30), data['num_people'], data['children'], 
               data['elderly'], data['disabilities'], data['mobility'], data['language'], data['location']))
    conn.commit()
    conn.close()
