import sqlite3

# Database Path
DB_PATH = "data/chicago_activities.db"

def db_names_to_ids(names, db_table):
    """
    Finds park IDs that match a list of park names.

    Args:
        names (list): List of park names.
        db_table: "parks" or "activities"

    Returns:
        list: List of matching park IDs.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Placeholders - each ? is a park to find
    placeholders = ','.join(['?'] * len(names))
    
    # Get and return IDs ("city_id"), flattened as list
    cur.execute(f"SELECT city_id FROM {db_table} WHERE name IN ({placeholders})", names)
    output = [row[0] for row in cur.fetchall()]
    conn.close()
    return output


def clean_park_facility_name(name):
    """
    Cleans park/facility name by fixing name abbreviations.

    Args:
        name (str): Raw location name.

    Returns:
        str: Cleaned location name.
    """
    if not name:
        return name
    
    _from = [" Ctr", " Pk", " Fld", " Cmty"]
    _to = [" Center", " Park", " Field", " Community"]
    
    for _from, _to in zip(_from, _to):
        name = name.replace(_from, _to)
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

    for activity in activities:
        location = activity.get("location")
        if location:
            if location not in park_activity_map:
                # If the fetched activity has a location returned,
                # Initialize mapping for that location
                park_activity_map[location] = []
            
            # Add activity to list of activities for that location
            park_activity_map[location].append(activity["name"])

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
