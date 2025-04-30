from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_session import Session
from app.scrape import ActivityScraper
from app.database_utils import get_activity_parks, DB_PATH
import sqlite3

app = Flask(__name__,
            template_folder="../templates",
            static_folder="../static")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Paths
DB_PATH = "data/chicago_activities.db"
SPATIALITE_PATH = "/opt/homebrew/lib/mod_spatialite.dylib"
RESULTS_PATH = "results.html"
INDEX_PATH = "index.html"

# Utility function: scrape activities based on form dat
def use_scraper(form_data, first_page=1):
    """Initializes and uses the ActivityScraper to fetch activities."""
    # Build location tuple using fetched address
    user_lat_list = form_data.get("user_lat", [None])
    user_lon_list = form_data.get("user_lon", [None])
    location = (
        float(user_lat_list[0]) if user_lat_list[0] else None,
        float(user_lon_list[0]) if user_lon_list[0] else None,
    )

    # Build distance using form 
    distance_list = form_data.get("distance", [None])
    distance_miles = float(distance_list[0]) if distance_list[0] else None

    # Build open spots using form
    open_slots_list = form_data.get('open_slots', [1])
    open_slots = int(open_slots_list[0]) if open_slots_list[0] else 1

    # Create scraper instance
    scraper = ActivityScraper(
        distance_miles=distance_miles,
        parks=form_data.get("parks", []),
        categories=form_data.get("categories", []),
        age_groups=form_data.get("age_groups", []),
        open_slots=open_slots,
        location=location,
        first_page=first_page
    )
    scraper.get_activities()
    scraper.dedeup_activities()
    return scraper.activities, scraper.more_results_to_fetch

# Route: Home page search form
@app.route("/", methods=["GET"])
def index():
    """Renders the main search page with parks, categories, and age groups."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        # Fetch park data
        cur.execute("SELECT name, latitude, longitude FROM parks")
        parks = [
            {"name": name, "latitude": latitude, "longitude": longitude}
            for name, latitude, longitude in cur.fetchall()
        ]

        # Fetch categories
        cur.execute("""
            SELECT DISTINCT activity 
            FROM activities 
            WHERE type = 'ActivityOtherCategoryID' 
            ORDER BY activity
        """)
        all_categories = [row[0] for row in cur.fetchall()]

        # Fetch age groups
        cur.execute("""
            SELECT DISTINCT activity 
            FROM activities 
            WHERE type = 'ActivityCategoryID' 
            ORDER BY activity
        """)
        all_age_groups = [row[0] for row in cur.fetchall()]

    return render_template(INDEX_PATH,
                           parks=parks,
                           all_categories=all_categories,
                           all_age_groups=all_age_groups,
                           open_slots=1)

# Route: Search activities
@app.route("/search", methods=["POST"])
def search():
    """Handles form submission and starts an activity search."""
    form_data = request.form.to_dict(flat=False)

    session["first_page"] = 1 

    activities, more_results_to_fetch = use_scraper(form_data)

    # Store form and activity results in session
    session["search_form"] = form_data
    session["activities"] = activities
    session["more_results_to_fetch"] = more_results_to_fetch

    return redirect(url_for("results"))

# Route: Results page
@app.route("/results")
def results():
    """Displays the list of found activities and park map."""
    activities = session.get("activities", [])
    activity_parks = get_activity_parks(activities)
    show_load_more = session.get("more_results_to_fetch", False)
    return render_template(RESULTS_PATH, activities=activities, activity_parks=activity_parks, show_load_more=show_load_more)

# Route: Load more activities
@app.route("/load_more", methods=["POST"])
def load_more():
    """Handles loading additional pages of activities."""
    request_data = request.get_json()
    current_page = request_data.get('page')

    if current_page is None:
        return jsonify({"success": False, "error": "Page number is missing"}), 400

    search_form = session.get("search_form", {})
    if not search_form:
        return jsonify({"success": False, "error": "Missing search parameters"}), 400

    # Fetch next batch of activities
    activities, more_results_to_fetch = use_scraper(search_form, first_page=int(current_page))

    if "activities" not in session:
        session["activities"] = []

    session["activities"].extend(activities)

    return jsonify({
        "success": True,
        "activities": activities, 
        "activity_parks": get_activity_parks(activities),
        "more_results_to_fetch": more_results_to_fetch
    })

# Route: Find nearby parks
@app.route("/find_nearby_parks", methods=["POST"])
def find_nearby_parks():
    """Finds parks near a given latitude/longitude."""
    data = request.get_json()
    lat, lon = data["lat"], data["lon"]
    radius = float(data.get("radius", 2)) * 1609.34  # Convert miles to meters

    query = """
        SELECT name, latitude, longitude
        FROM parks
        WHERE 6371000 * acos(
            cos(radians(?)) * cos(radians(latitude)) *
            cos(radians(longitude) - radians(?)) +
            sin(radians(?)) * sin(radians(latitude))
        ) <= ?
    """

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(query, (lat, lon, lat, radius))
        results = cur.fetchall()

    return jsonify({
        "success": True,
        "parks": [
            {"name": name, "latitude": latitude, "longitude": longitude}
            for name, latitude, longitude in results
        ]
    })

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5002)