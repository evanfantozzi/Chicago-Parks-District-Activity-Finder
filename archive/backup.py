import httpx
from pprint import pprint
import json

# Base URL for search
url = "https://anc.apm.activecommunities.com/chicagoparkdistrict/rest/activities/list?locale=en-US"

# Specify search
page_info = {
    "order_by": "Name",
    "page_number": 1,  # Add page number here
    "total_records_per_page": 20
}

headers = {
    "Content-Type": "application/json;charset=utf-8",
    "X-Requested-With": "XMLHttpRequest",
    "page_info": json.dumps(page_info)  # Convert dict to JSON string
}

# Specify search filters
payload = {
    "activity_search_pattern": {
        "skills": [],
        "time_after_str": "",
        "days_of_week": "",
        "activity_select_param": None,
        "center_ids": [],
        "time_before_str": "",
        "open_spots": None,
        "activity_id": None,
        "activity_category_ids": [],
        "date_before": "",
        "min_age": None,
        "date_after": "",
        "activity_type_ids": [],
        "site_ids": [],
        "for_map": False,
        "geographic_area_ids": [],
        "season_ids": [],
        "activity_department_ids": [],
        "activity_other_category_ids": [],
        "child_season_ids": [],
        "activity_keyword": "",
        "instructor_ids": [],
        "max_age": None,
        "custom_price_from": "",
        "custom_price_to": "",
    },
    "activity_transfer_pattern": {},
}


# Get response
response = httpx.post(url, headers=headers, json=payload)
data = response.json()
if "body" in data:
    activities = []
    
    # Get and check for activity items 
    activity_items = data["body"].get("activity_items", [])
    if activity_items:
        
        # Loop through each activity, store in list of dicts of activities
        for activity_data in activity_items:
            activity = {
                'id': activity_data.get('id'),
                'name': activity_data.get('name'),
                'desc': activity_data.get('desc'),
                'age_description': activity_data.get('age_description'),
                'category': activity_data.get('category'),
                'date_range': activity_data.get('date_range'),
                'time_range': activity_data.get('time_range'),
                'location': activity_data['location'].get('label') if 'location' in activity_data else None,
                'detail_url': activity_data.get('detail_url'),
                'action_link': activity_data.get('action_link', {}).get('href') if activity_data.get('action_link') else None
            }
            activities.append(activity)
    
        pprint(activities)
        
        
    else:
        print("No activities found in the body.")
else:
    print("No body in the response data")
    print("Response JSON keys:", data.keys())

