import sqlite3
import httpx 
import json
import time
from datetime import datetime
from datetime import time as dtime
import os

class ActivityScraper:
    def __init__(self, 
                 distance_miles=None,
                 distance_km=None,
                 parks=[], 
                 location=(41.7943, -87.5907),
                 categories=[], 
                 age_groups=[], 
                 open_spots=1, 
                 min_age=None, 
                 max_age=None, 
                 days_of_week=None, 
                 order_by="Name",
                 first_page=1):
        
        self.db_path = "chicago_activities.db"
        self.location = location  # (lat, lon)

        self.first_page = first_page
        self.order_by = order_by
        self.base_url = "https://anc.apm.activecommunities.com/chicagoparkdistrict/rest/activities/list?locale=en-US"
        self.headers = {
            "Content-Type": "application/json;charset=utf-8",
            "X-Requested-With": "XMLHttpRequest",
        }

        # Binary trackers to check if we are adding in parameters 
        self.all_categories = False
        self.all_age_groups = False 
        self.all_parks = False
        
        # Allow for "all" options
        if categories:
            self.categories = self.get_activity_ids_by_name(categories)
        else:
            self.all_categories = True
            self.categories = None
        
        if age_groups:
            self.age_groups = self.get_activity_ids_by_name(age_groups)
        else:
            self.all_age_groups = True
            self.age_groups = None
            
        
        self.open_spots = open_spots
        self.min_age = min_age
        self.max_age = max_age
        self.days_of_week = days_of_week
        
        
        # Parks
        if parks == "[All]":
            self.parks = []
            self.all_parks=True 
        elif parks:
            self.set_park_ids_by_name(parks) 
        else:
            self.set_park_ids_by_distance(distance_miles, distance_km)

        # List of activities to return
        self.activities = []

    def get_sqlite_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.enable_load_extension(True)
        conn.load_extension(os.getenv("SPATIALITE_PATH", "mod_spatialite")) 
        return conn

    def set_park_ids_by_distance(self, distance_miles=5, distance_km=0):
        """
        Set list of parks equal to those within given miles/kilometers using Haversine distance
        """
        # Convert distance to meters
        if distance_miles:
            distance_meters = distance_miles * 1609.34
        else:
            distance_meters = distance_km * 1000

        lat, lon = self.location  # user location

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

        conn = self.get_sqlite_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        self.parks = [row[0] for row in cur.fetchall()]
        conn.close()

    def set_park_ids_by_name(self, names):
        conn = self.get_sqlite_connection()
        cur = conn.cursor()
        placeholders = ','.join(['?'] * len(names))
        cur.execute(f"SELECT city_id FROM parks WHERE name IN ({placeholders})", names)
        self.parks = [row[0] for row in cur.fetchall()]
        conn.close()

    def get_activity_ids_by_name(self, names):
        if not names:
            return []
        conn = self.get_sqlite_connection()
        cur = conn.cursor()
        placeholders = ','.join(['?'] * len(names))
        cur.execute(f"SELECT city_id FROM activities WHERE activity IN ({placeholders})", names)
        ids = [row[0] for row in cur.fetchall()]
        conn.close()
        return ids

    def set_headers_and_payload(self):
        self.headers["page_info"] = json.dumps({
            "order_by": self.order_by,
            "total_records_per_page": 20
        })

        self.payload = {
            "activity_search_pattern": {
                "activity_select_param": 2,
                "days_of_week": self.days_of_week,
                "center_ids": self.parks,
                "open_spots": self.open_spots,
                "activity_id": None,
                "activity_category_ids": self.age_groups,
                "min_age": self.min_age,
                "activity_other_category_ids": self.categories,
                "max_age": self.max_age,
            },
            "activity_transfer_pattern": {}
        }


    def dedeup_activities(self):
        old_activities = self.activities
        grouped = {}

        for activity in old_activities:
            key = (
                activity["name"],
                activity["location"],
                activity["category"],
                activity["age_description"]
            )

            if key not in grouped:
                grouped[key] = {
                    "name": activity["name"],
                    "location": activity["location"],
                    "desc": activity["desc"],
                    "category": activity["category"],
                    "age_description": activity["age_description"],
                    "date_ranges": [],
                    "time_ranges": [],
                    "action_links": [],
                    "detail_links": [],
                    "days": []
                }

            grouped[key]["date_ranges"].append(activity.get("date_range", ""))
            grouped[key]["time_ranges"].append(activity.get("time_range", ""))
            grouped[key]["action_links"].append(activity.get("action_link"))
            grouped[key]["detail_links"].append(activity.get("detail_url"))
            grouped[key]["days"].append(activity.get("days_of_week", ""))  # include here

        for act in grouped.values():
            sessions = []

            for i in range(len(act["date_ranges"])):
                date_text = act["date_ranges"][i]
                time_text = act["time_ranges"][i]

                # Try parsing date
                try:
                    start_date_str = date_text.split(" to ")[0].strip()
                    start_date = datetime.strptime(start_date_str, "%B %d, %Y")
                except Exception:
                    start_date = datetime(1900, 1, 1)

                # Try parsing time
                try:
                    start_time_str = time_text.split(" - ")[0].strip()
                    # Special handling for "Noon"
                    if start_time_str.lower() == "noon":
                        start_time = dtime(12, 0)
                    else:
                        start_time = datetime.strptime(start_time_str, "%I:%M %p").time()
                except Exception:
                    start_time = dtime(0, 0)

                weekday = start_date.strftime("%A")
                labeled_date = f"{date_text} ({weekday})"

                sessions.append((
                    start_date,
                    start_time,
                    labeled_date,
                    act["time_ranges"][i],
                    act["action_links"][i],
                    act["detail_links"][i],
                    act["days"][i]
                ))

            sessions.sort()

            if sessions:
                (
                    _,
                    _,
                    act["date_ranges"],
                    act["time_ranges"],
                    act["action_links"],
                    act["detail_links"],
                    act["days"]
                ) = map(list, zip(*sessions))
            else:
                act["date_ranges"] = []
                act["time_ranges"] = []
                act["action_links"] = []
                act["detail_links"] = []
                act["days"] = []

        self.activities = list(grouped.values())




    def get_activities(self):
        max_pages = 5
        records_per_page = 20

        self.set_headers_and_payload()

        if not self.all_parks and not self.parks:
            return None
        if not self.all_age_groups and not self.age_groups:
            return None
        if not self.all_categories and not self.categories:
            return None

        seen_sessions = set()

        for page_num in range(self.first_page, self.first_page + max_pages + 1):
            self.payload["page_number"] = page_num
            response = httpx.post(self.base_url, headers=self.headers, json=self.payload)
            data = response.json()

            items = data.get("body", {}).get("activity_items", [])
            if not items:
                break

            for activity_data in items:
                key = (
                    activity_data.get('name'),
                    activity_data.get('location', {}).get('label'),
                    activity_data.get('date_range'),
                    activity_data.get('time_range'),
                )

                if key in seen_sessions:
                    continue
                seen_sessions.add(key)

                self.activities.append({
                    'id': activity_data.get('id'),
                    'name': activity_data.get('name'),
                    'desc': activity_data.get('desc'),
                    'age_description': activity_data.get('age_description'),
                    'category': activity_data.get('category'),
                    'date_range': activity_data.get('date_range'),
                    'time_range': activity_data.get('time_range'),
                    'location': activity_data.get('location', {}).get('label'),
                    'detail_url': activity_data.get('detail_url'),
                    'action_link': activity_data.get('action_link', {}).get('href') if activity_data.get('action_link') else None
                })

            if len(items) < records_per_page:
                break
            else:
                time.sleep(1)

        self.dedeup_activities()
    
    def __str__(self):
        return json.dumps(self.activities, indent=2)
    