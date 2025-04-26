from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from scrape import ActivityScraper
from activity_parks import get_activity_parks
import sqlite3
from flask_session import Session

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Use a secure key in production
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

SPATIALITE_PATH = "/opt/homebrew/lib/mod_spatialite.dylib"
DB_PATH = "chicago_activities.db"
RESULTS_PATH = "results.html"
INDEX_PATH = "index.html"

def use_scraper(form_data):
    scraper = ActivityScraper(
        distance_miles=form_data.get("distance", type=float),
        parks=form_data.getlist("parks"),
        categories=form_data.getlist("categories"),
        age_groups=form_data.getlist("age_groups"),
        open_spots=form_data.get("open_spots", type=int) or 1,
        location=(
            form_data.get("user_lat", type=float),
            form_data.get("user_lon", type=float),
        )
    )
    scraper.get_activities()
    return scraper.activities

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

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        activities = use_scraper(request.form)
        session["activities"] = activities
        return redirect(url_for("results"))

    else:
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

@app.route("/results")
def results():
    activities = session.get("activities", [])
    activity_parks = get_activity_parks(activities)
    
    return render_template(RESULTS_PATH, activities=activities, activity_parks=activity_parks)

if __name__ == "__main__":
    app.run(debug=True)
