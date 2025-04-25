import sqlite3
import csv
import jellyfish
import httpx
import time

CSV_FILE = "searchables.csv"
DB_FILE = "parks.db"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "your-app-name"  # Update this to your name/app/email

def fetch_coordinates(client, full_address):
    params = {
        "q": full_address,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": USER_AGENT
    }

    try:
        response = client.get(NOMINATIM_URL, params=params, headers=headers)
        response.raise_for_status()
        results = response.json()
        if results:
            return results[0]["lat"], results[0]["lon"]
    except httpx.HTTPError as e:
        print(f"Error fetching from Nominatim: {e}")
    return None, None

def main():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM filterable_parks;")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='filterable_parks';")
    conn.commit()

    with httpx.Client() as client:
        with open(CSV_FILE, newline='') as f:
            reader = csv.DictReader(f, fieldnames=["park"])
            for row in reader:
                search_name = row['park']

                # Fetch all parks from the scraped table
                cursor.execute("SELECT title, address FROM parks_scraped")
                rows = cursor.fetchall()

                if not rows:
                    print(f"No parks found in parks_scraped for {search_name}")
                    continue

                # Get best fuzzy match
                best_match = max(rows, key=lambda r: jellyfish.jaro_winkler_similarity(search_name, r[0]))
                matched_title, matched_address = best_match
                print(f"Matched '{search_name}' to '{matched_title}'")

                # Full address for Nominatim
                full_address = f"{matched_address}, Chicago, IL"
                lat, lon = fetch_coordinates(client, full_address)
                time.sleep(3)  # Be nice to Nominatim

                if lat and lon:
                    cursor.execute("""
                        INSERT INTO filterable_parks (name, longitude, latitude, address)
                        VALUES (?, ?, ?, ?)
                    """, (search_name, lon, lat, matched_address))
                    conn.commit()
                    print(f"   Inserted '{search_name}' at coords: {lat}, {lon}")
                else:
                    print("   Couldn't match using", matched_address, "- Trying again with name:", search_name)
                    full_address = f"{search_name}, Chicago, IL"
                    lat, lon = fetch_coordinates(client, full_address)
                    if lat and lon:
                        cursor.execute("""
                            INSERT INTO filterable_parks (name, longitude, latitude, address)
                            VALUES (?, ?, ?, ?)
                        """, (search_name, lon, lat, matched_address))
                        conn.commit()
                        print(f"   Inserted '{search_name}' at coords: {lat}, {lon}")
                    else:
                        print("Couldn't match", search_name)

    conn.close()

if __name__ == "__main__":
    main()
