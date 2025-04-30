import httpx
import json
from time import sleep
from datetime import datetime, time 

from app.database_utils import (
    set_park_ids_by_distance,
    set_park_ids_by_name,
    get_activity_ids_by_name,
    normalize_location_name
)

class ActivityScraper:
    """
    A class to scrape activities from the Chicago Park District system.
    Fetches and organizes activities based on parks, distance, categories, age groups, etc.
    """
    MAX_PAGES = 5
    RECORDS_PER_PAGE = 20

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
        """
        Initializes an ActivityScraper instance with search filters and default settings.
        """
        # Default search parameters
        self.db_path = "data/chicago_activities.db"
        self.location = location
        self.first_page = first_page
        self.order_by = order_by
        self.base_url = "https://anc.apm.activecommunities.com/chicagoparkdistrict/rest/activities/list?locale=en-US"
        self.headers = {
            "Content-Type": "application/json;charset=utf-8",
            "X-Requested-With": "XMLHttpRequest",
        }

        # Binary flags - for whether all categories/age groups/parks were searched
        self.all_categories = False
        self.all_age_groups = False 
        self.all_parks = False

        # Set to true if last page of searches reached and still have more results
        self.more_results_to_fetch = False

        # If any categories/age groups passed in, convert their names to IDs
        if categories:
            self.categories = get_activity_ids_by_name(categories, self.db_path)
        else:
            self.all_categories = True
            self.categories = None
        
        if age_groups:
            self.age_groups = get_activity_ids_by_name(age_groups, self.db_path)
        else:
            self.all_age_groups = True
            self.age_groups = None
        
        # Open spots preset to 1
        self.open_spots = open_spots
        
        # Other search queries - unused for now 
        self.min_age = min_age
        self.max_age = max_age
        self.days_of_week = days_of_week

        # Convert list of park names to IDs
        if parks == "[All]":
            self.parks = []
            self.all_parks = True 
        elif parks:
            self.parks = set_park_ids_by_name(parks, self.db_path)
        else:
            self.parks = set_park_ids_by_distance(self.location, distance_miles, distance_km, self.db_path)

        self.activities = []

    def can_search(self):
        """
        Confirms that for each of parks, age_groups, categories, there is always
        either "all" selected or at least one specified
        """
        return ((self.all_parks or self.parks) and 
                (self.all_age_groups or self.age_groups) and 
                (self.all_categories or self.categories))

    def build_headers(self, page_num):
        """
        Takes in page number and builds headers in scraper
        """
        headers = self.headers.copy()
        headers["page_info"] = json.dumps({
            "order_by": self.order_by,
            "total_records_per_page": self.RECORDS_PER_PAGE,
            "page_number": page_num
        })
        return headers

    def initialize_group(self, activity):
        """
        Initializes a group structure to aggregate multiple sessions of the same activity.
        """
        return {
            "name": activity["name"],
            "location": activity["location"],
            "desc": activity["desc"],
            "category": activity["category"],
            "age_description": activity["age_description"],
            "sessions": []
        }

    def parse_session(self, date_text, time_text):
        """
        Parses session start date and time from text formats.
        """
        try:
            start_date_str = date_text.split(" to ")[0].strip()
            start_date = datetime.strptime(start_date_str, "%B %d, %Y")
        except Exception:
            start_date = datetime(1900, 1, 1)

        try:
            start_time_str = time_text.split(" - ")[0].strip()
            if start_time_str.lower() == "noon":
                start_time = time(12, 0)
            else:
                start_time = datetime.strptime(start_time_str, "%I:%M %p").time()
        except Exception:
            start_time = time(0, 0)

        return start_date, start_time

    def build_sorted_sessions(self, session_list):
        """
        Sorts a list of session dictionaries by start date and time.
        """
        sessions = []

        for session in session_list:
            start_date, start_time = self.parse_session(session["date_range"], session["time_range"])
            weekday = start_date.strftime("%A")
            labeled_date = f"{session['date_range']} ({weekday})"

            sessions.append((
                start_date,
                start_time,
                labeled_date,
                session["time_range"],
                session["action_link"],
                session["detail_link"],
                session["days"]
            ))

        sessions.sort()
        return sessions

    def unpack_sessions(self, sorted_sessions):
        """
        Unpacks a sorted session list into individual session attributes.
        """
        date_ranges = []
        time_ranges = []
        action_links = []
        detail_links = []
        days_list = []

        for sorted_session in sorted_sessions:
            date_ranges.append(sorted_session[2])
            time_ranges.append(sorted_session[3])
            action_links.append(sorted_session[4])
            detail_links.append(sorted_session[5])
            days_list.append(sorted_session[6])

        return date_ranges, time_ranges, action_links, detail_links, days_list

    def parse_activity(self, activity_data):
        """
        Parses an activity JSON object into a clean dictionary format.
        """
        return {
            "id": activity_data.get("id"),
            "name": activity_data.get("name"),
            "desc": activity_data.get("desc"),
            "age_description": activity_data.get("age_description"),
            "category": activity_data.get("category"),
            "date_range": activity_data.get("date_range"),
            "time_range": activity_data.get("time_range"),
            "location": normalize_location_name(activity_data.get("location", {}).get("label")),
            "detail_url": activity_data.get("detail_url"),
            "action_link": activity_data.get("action_link", {}).get("href") if activity_data.get("action_link") else None,
            "days_of_week": activity_data.get("days_of_week", "")
        }

    def set_payload(self):
        """
        Constructs the payload for the search request based on parameters.
        """
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

    def build_session(self, activity):
        """
        Builds a single session dictionary from a parsed activity.
        """
        return {
            "date_range": activity.get("date_range", ""),
            "time_range": activity.get("time_range", ""),
            "action_link": activity.get("action_link"),
            "detail_link": activity.get("detail_url"),
            "days": activity.get("days_of_week", "")
        }

    def dedeup_activities(self):
        """
        Deduplicates activities by grouping multiple sessions of the same activity.
        """
        # List of grouped activities
        grouped = {}

        for activity in self.activities:
            # Determine uniqueness using name/location/category/age description
            key = (
                activity["name"],
                activity["location"],
                activity["category"],
                activity["age_description"]
            )

            # Create new "group" if not found
            if key not in grouped:
                grouped[key] = self.initialize_group(activity)

            # Within that key grouping, add a session of the activity
            grouped[key]["sessions"].append(self.build_session(activity))

        
        # Replace activities with grouped activities
        self.activities = []
        for activity in grouped.values():
            # For each grouped activity, sort the sessions
            sorted_sessions = self.build_sorted_sessions(activity["sessions"])
            date_ranges, time_ranges, action_links, detail_links, days_list = self.unpack_sessions(sorted_sessions)
            del activity["sessions"]

            # Set lists of dates/times/links/days of week for activity
            activity["date_ranges"] = date_ranges
            activity["time_ranges"] = time_ranges
            activity["action_links"] = action_links
            activity["detail_links"] = detail_links
            activity["days"] = days_list

            self.activities.append(activity)

    def get_activities(self):
        """
        Main function that executes the scraping of activities based on filters.
        """
        if not self.can_search():
            # Double check that at least one location selected, 
            # and that for categories/age groups either "all" or at 1+ specified values
            return None

        self.set_payload()

        # Loop through 5 pages of results (100 results)
        for page_num in range(self.first_page, self.first_page + self.MAX_PAGES):

            # Make request, confirm that response has items
            response = httpx.post(self.base_url, headers=self.build_headers(page_num), json=self.payload)
            data = response.json()
            items = data.get("body", {}).get("activity_items", [])
            if not items:
                break

            # Parse activity and append to activities list
            for activity_data in items:
                self.activities.append(self.parse_activity(activity_data))

            if len(items) < self.RECORDS_PER_PAGE:
                # If reached end of results, break out of loop
                break
            elif page_num == self.first_page + self.MAX_PAGES - 1 and len(items) == self.RECORDS_PER_PAGE:
                # Got max results on last page, assume there are more results to fetch
                self.more_results_to_fetch = True
            else:
                # Otherwise sleep and iterate
                sleep(1)

    def __str__(self):
        return json.dumps(self.activities, indent=2)
