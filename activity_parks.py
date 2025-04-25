import sqlite3
DB_PATH = "chicago_activities.db"

def get_activity_parks(activities):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    park_activity_map = {}
    for a in activities:
        loc = a.get("location")
        if loc:
            if loc not in park_activity_map:
                park_activity_map[loc] = []
            park_activity_map[loc].append(a["name"])

    park_names = list(park_activity_map.keys())
    placeholders = ",".join("?" for _ in park_names)

    cursor.execute(f"""
        SELECT name, latitude, longitude
        FROM parks
        WHERE name IN ({placeholders})
    """, park_names)

    results = []
    for name, lat, lon in cursor.fetchall():
        act_names = park_activity_map.get(name, [])
        results.append((name, lat, lon, act_names))

    conn.close()
    return results