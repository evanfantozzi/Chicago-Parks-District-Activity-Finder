import httpx
import json
from time import sleep
from datetime import datetime, time 

from app.database_utils import (
    db_names_to_ids,
    clean_park_facility_name
)

class ActivityScraper:
    """
    A class to scrape activities from the Chicago Park District system.
    Fetches and organizes activities based on parks, distance, categories, age groups, etc.
    """
    MAX_PAGES_PER_SCRAPE = 5 # Show 5 pages of results at a time 
    RECORDS_PER_PAGE = 20 # Each page has 20 results

    def __init__(self, 
                 distance_miles=None, # Not using at the moment
                 distance_km=None, # Not using at the moment
                 parks=[], # List of desired parks/facilities
                 location=(41.7943, -87.5907), # Default to downtown
                 categories=[], # List of desired activity categories
                 age_groups=[], # List of desired activity age groups
                 open_slots=1, # How many slots needed for activity
                 min_age=None, # Not using at the moment
                 max_age=None, # Not using at the moment
                 days_of_week=None, # Not using at the moment
                 order_by="Name", # Not using at the moment
                 first_page=1 # First page to start scraping
                 ): 

        # Default search parameters
        self.location = location
        self.first_page = first_page
        self.order_by = order_by
        self.base_url = "https://anc.apm.activecommunities.com/chicagoparkdistrict/rest/activities/list?locale=en-US"
        self.headers = {
            "Content-Type": "application/json;charset=utf-8",
            "X-Requested-With": "XMLHttpRequest",
        }

        # Binary flag - set to true if last page of searches reached and still have more results
        self.more_results_to_fetch = False

        # If specific categories/age groups passed in, convert their names to IDs
        self.categories = db_names_to_ids(categories, "activities") if categories else []
        self.age_groups = db_names_to_ids(age_groups, "activities") if age_groups else []

        # Open slots preset to 1
        self.open_slots = open_slots
        
        # Other search queries - unused for now 
        self.min_age = min_age
        self.max_age = max_age
        self.days_of_week = days_of_week

        # Convert list of park names to IDs
        self.parks = db_names_to_ids(parks, "parks")

        # To fill with self.get_activities()
        self.activities = []

    def build_headers(self, page_num):
        """
        Takes in page number and builds headers for scraper
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

    def start_date_time(self, date_text, time_text):
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

    def build_sorted_sessions_list(self, session_list):
        """
        Sorts a list of session dictionaries by start date and time.
        """
        sessions = []

        for session in session_list:
            start_date, start_time = self.start_date_time(session["date_range"], session["time_range"])
            weekday = start_date.strftime("%A")
            
            if " to " in session["date_range"]:
                # Repeating event 
                date_range = f"{session['date_range']} ({weekday}s)"
            else:
                # One off event
                date_range = f"{session['date_range']} ({weekday})"

            # Append information to include in sorted session table on results page
            sessions.append((
                
                # Start_date and time only used for sorting (not kept)
                start_date,
                start_time,
                
                # Returned per activity after sorting
                date_range,
                session["time_range"],
                session["action_link"],
                session["detail_link"],
                session["days"]
            ))
            
        # Sort and return date_range, time_range, action link, detail_link, days
        sessions.sort()
        return [session[2:] for session in sessions]

    def unpack_sessions(self, sorted_sessions):
        """
        Unpacks a sorted session list into individual session attributes.
        """
        date_ranges = []
        time_ranges = []
        action_links = []
        detail_links = []
        days = []

        for sorted_session in sorted_sessions:
            date_range, time_range, action_link, detail_link, day = sorted_session
            
            date_ranges.append(date_range)
            time_ranges.append(time_range)
            action_links.append(action_link)
            detail_links.append(detail_link)
            days.append(day)

        return date_ranges, time_ranges, action_links, detail_links, days

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
            "location": clean_park_facility_name(activity_data.get("location", {}).get("label")),
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
                "activity_select_param": 2, # Type of results returned, standard
                "center_ids": self.parks,
                "open_spots": self.open_slots,
                "activity_category_ids": self.age_groups,
                "activity_other_category_ids": self.categories,
                # "activity_id": None, # Not currently using in our query format
                # "days_of_week": self.days_of_week, - Not currently used
                # "min_age": self.min_age, - Not currently used
                # "max_age": self.max_age, - Not currently used
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
            sorted_sessions = self.build_sorted_sessions_list(activity["sessions"])
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

        self.set_payload()

        # Loop through 5 pages of results (100 results)
        for page_num in range(self.first_page, self.first_page + self.MAX_PAGES_PER_SCRAPE):

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
            elif page_num == self.first_page + self.MAX_PAGES_PER_SCRAPE - 1 and len(items) == self.RECORDS_PER_PAGE:
                # Got max results on last page, assume there are more results to fetch
                self.more_results_to_fetch = True
            else:
                # Otherwise sleep and iterate
                sleep(1)

    def __str__(self):
        return json.dumps(self.activities, indent=2)
