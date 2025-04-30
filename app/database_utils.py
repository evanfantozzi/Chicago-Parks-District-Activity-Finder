import sqlite3
import os

# Database Path
DB_PATH = "data/chicago_activities.db"

def get_sqlite_connection(db_path=DB_PATH):
    """
    Opens a connection to the SQLite database with SpatiaLite extension enabled.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        sqlite3.Connection: Database connection object.
    """
    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    if os.getenv("RENDER") == "true":
        conn.load_extension(os.getenv("SPATIALITE_PATH", "/usr/lib/x86_64-linux-gnu/mod_spatialite"))
    else:
        conn.load_extension(os.getenv("SPATIALITE_PATH", "/opt/homebrew/lib/mod_spatialite.dylib"))
    return conn

def set_park_ids_by_distance(location, distance_miles=None, distance_km=0, db_path=DB_PATH):
    """
    Finds parks within a specified distance from a location.

    Args:
        location (tuple): (latitude, longitude) pair.
        distance_miles (float, optional): Distance radius in miles.
        distance_km (float, optional): Distance radius in kilometers.
        db_path (str): Path to the SQLite database file.

    Returns:
        list: List of park IDs within the given distance.
    """
    if distance_miles:
        distance_meters = distance_miles * 1609.34
    else:
        distance_meters = distance_km * 1000

    lat, lon = location

    query = """
    SELECT city_id
    FROM parks
    WHERE
        6371000 * acos(
            cos(radians(?)) * cos(radians(latitude)) *
            cos(radians(longitude) - radians(?)) +
            sin(radians(?)) * sin(radians(latitude))
        ) <= ?
    """

    params = (lat, lon, lat, distance_meters)

    conn = get_sqlite_connection(db_path)
    cur = conn.cursor()
    cur.execute(query, params)
    parks = [row[0] for row in cur.fetchall()]
    conn.close()
    return parks

def set_park_ids_by_name(names, db_path=DB_PATH):
    """
    Finds park IDs that match a list of park names.

    Args:
        names (list): List of park names.
        db_path (str): Path to the SQLite database file.

    Returns:
        list: List of matching park IDs.
    """
    conn = get_sqlite_connection(db_path)
    cur = conn.cursor()
    placeholders = ','.join(['?'] * len(names))
    cur.execute(f"SELECT city_id FROM parks WHERE name IN ({placeholders})", names)
    parks = [row[0] for row in cur.fetchall()]
    conn.close()
    return parks

def get_activity_ids_by_name(names, db_path=DB_PATH):
    """
    Finds activity IDs that match a list of activity names.

    Args:
        names (list): List of activity names.
        db_path (str): Path to the SQLite database file.

    Returns:
        list: List of matching activity IDs.
    """
    if not names:
        return []
    conn = get_sqlite_connection(db_path)
    cur = conn.cursor()
    placeholders = ','.join(['?'] * len(names))
    cur.execute(f"SELECT city_id FROM activities WHERE activity IN ({placeholders})", names)
    ids = [row[0] for row in cur.fetchall()]
    conn.close()
    return ids

def normalize_location_name(name):
    """
    Normalizes a location name by expanding common abbreviations.

    Args:
        name (str): Raw location name.

    Returns:
        str: Normalized location name.
    """
    if not name:
        return name
    replacements = {
        " Ctr": " Center",
        " Pk": " Park",
        " Fld": " Field",
        " Cmty": " Community"
    }
    for short, full in replacements.items():
        name = name.replace(short, full)
    return name

def get_activity_parks(activities):
    """
    Maps activities to their corresponding parks and retrieves park coordinates.

    Args:
        activities (list): List of activity dictionaries, each containing a 'location' key.

    Returns:
        list: A list of tuples containing (park name, latitude, longitude, list of associated activity names).
    """
    # Connect to the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create a mapping from park location name to list of activity names
    park_activity_map = {}

    for a in activities:
        loc = a.get("location")
        if loc:
            if loc not in park_activity_map:
                park_activity_map[loc] = []
            park_activity_map[loc].append(a["name"])

    # Prepare the list of park names to query
    park_names = list(park_activity_map.keys())
    placeholders = ",".join("?" for _ in park_names)

    # Fetch park latitude and longitude for each park name
    cursor.execute(f"""
        SELECT name, latitude, longitude
        FROM parks
        WHERE name IN ({placeholders})
    """, park_names)

    # Build results with park name, coordinates, and associated activities
    results = []
    for name, lat, lon in cursor.fetchall():
        act_names = park_activity_map.get(name, [])
        results.append((name, lat, lon, act_names))

    # Close the database connection
    conn.close()

    return results
