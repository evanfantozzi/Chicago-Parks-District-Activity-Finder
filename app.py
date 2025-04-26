from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from scrape import ActivityScraper
from activity_parks import get_activity_parks
import sqlite3
from flask_session import Session
import logging

# Set up basic logging configuration for Flask
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Use a secure key in production
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

SPATIALITE_PATH = "/opt/homebrew/lib/mod_spatialite.dylib"
DB_PATH = "chicago_activities.db"
RESULTS_PATH = "results.html"
INDEX_PATH = "index.html"

# Utility function: scrape activities
def use_scraper(form_data, first_page=1):
    distance_list = form_data.get("distance", [None])
    distance_miles = float(distance_list[0]) if distance_list[0] else None

    parks = form_data.get("parks", [])
    categories = form_data.get("categories", [])
    age_groups = form_data.get("age_groups", [])

    open_spots_list = form_data.get("open_spots", [1])
    open_spots = int(open_spots_list[0]) if open_spots_list[0] else 1

    user_lat_list = form_data.get("user_lat", [None])
    user_lon_list = form_data.get("user_lon", [None])
    location = (
        float(user_lat_list[0]) if user_lat_list[0] else None,
        float(user_lon_list[0]) if user_lon_list[0] else None,
    )

    scraper = ActivityScraper(
        distance_miles=distance_miles,
        parks=parks,
        categories=categories,
        age_groups=age_groups,
        open_spots=open_spots,
        location=location,
        first_page=first_page
    )
    scraper.get_activities()
    return scraper.activities, scraper.more_results_to_fetch


# "/" Route: Show the blank search form
@app.route("/", methods=["GET"])
def index():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        cur.execute("SELECT name, latitude, longitude FROM parks")
        parks = [
            {"name": name, "latitude": latitude, "longitude": longitude}
            for name, latitude, longitude in cur.fetchall()
        ]

        cur.execute("""
            SELECT DISTINCT activity 
            FROM activities 
            WHERE type = 'ActivityOtherCategoryID' 
            ORDER BY activity
        """)
        all_categories = [row[0] for row in cur.fetchall()]

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
                           open_spots=1)


# "/search" Route: Scrape activities based on user search
@app.route("/search", methods=["POST"])
def search():
    # turn incoming form into a dict-of-lists so use_scraper always sees lists
    form_data = request.form.to_dict(flat=False)

    # Reset first page to 1 when a new search is made
    session["first_page"] = 1  # Reset the page number for a new search

    activities, more_results_to_fetch = use_scraper(form_data)

    # stash everything in session
    session["search_form"] = form_data
    session["activities"] = activities
    session["more_results_to_fetch"] = more_results_to_fetch

    return redirect(url_for("results"))


# "/results" Route: Show activities and map
@app.route("/results")
def results():
    activities = session.get("activities", [])
    activity_parks = get_activity_parks(activities)
    show_load_more = session.get("more_results_to_fetch", False)
    return render_template(RESULTS_PATH, activities=activities, activity_parks=activity_parks, show_load_more=show_load_more)


# "/load_more" Route: Load next batch of activities
@app.route("/load_more", methods=["POST"])
def load_more():
    # Get the page number from the request body
    request_data = request.get_json()
    current_page = request_data.get('page')  # Page sent by the client

    if current_page is None:
        logging.error("Page number is missing in the request.")
        return jsonify({"error": "Page number is missing"}), 400

    # Fetch the activities for the requested page
    search_form = session.get("search_form", {})
    if not search_form:
        return jsonify({"error": "Missing search parameters"}), 400

    # Fetch the activities based on the page number
    activities, more_results_to_fetch = use_scraper(search_form, first_page=current_page)

    # Append the new activities to the existing list in the session
    if "activities" not in session:
        session["activities"] = []

    session["activities"].extend(activities)

    # Log current page for debugging
    logging.debug(f"Fetched activities for page {current_page}. Total activities so far: {len(session['activities'])}")

    # Return the updated data to the client
    return jsonify({
        "activities": activities,  # Send only the activities for this page
        "activity_parks": get_activity_parks(activities),
        "more_results_to_fetch": more_results_to_fetch
    })


# "/find_nearby_parks" Route: Help users find nearby parks
@app.route("/find_nearby_parks", methods=["POST"])
def find_nearby_parks():
    data = request.get_json()
    lat, lon = data["lat"], data["lon"]
    radius = float(data.get("radius", 2)) * 1609.34  # miles to meters

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

    return jsonify([
        {"name": name, "latitude": latitude, "longitude": longitude}
        for name, latitude, longitude in results
    ])


if __name__ == "__main__":
    app.run(debug=True)
