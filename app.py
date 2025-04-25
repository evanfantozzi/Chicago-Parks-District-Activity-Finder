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


@app.route("/nearby_parks", methods=["POST"])
def nearby_parks():
    data = request.get_json()
    lat = data["lat"]
    lon = data["lon"]
    radius_meters = float(data.get("radius", 2)) * 1609.34

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT name, latitude, longitude
    FROM parks
    WHERE
        6371000 * acos(
            cos(radians(?)) * cos(radians(latitude)) *
            cos(radians(longitude) - radians(?)) +
            sin(radians(?)) * sin(radians(latitude))
        ) <= ?
    """
    cursor.execute(query, (lat, lon, lat, radius_meters))
    results = cursor.fetchall()
    conn.close()

    return jsonify([
        {"name": name, "latitude": latitude, "longitude": longitude}
        for name, latitude, longitude in results
    ])


@app.route("/", methods=["GET", "POST"])
def index():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT name, latitude, longitude FROM parks")
    parks = [
    {"name": name, "latitude": latitude, "longitude": longitude}
    for name, latitude, longitude in cur.fetchall()
]
    open_spots = 1 # placeholder

    cur.execute("""
        SELECT DISTINCT activity 
        FROM activities 
        WHERE type = 'ActivityOtherCategoryID' 
        ORDER BY activity
    """)
    activity_names = [row[0] for row in cur.fetchall()]

    cur.execute("""
        SELECT DISTINCT activity 
        FROM activities 
        WHERE type = 'ActivityCategoryID' 
        ORDER BY activity
    """)
    age_groups = [row[0] for row in cur.fetchall()]
    conn.close()

    if request.method == "POST":
        distance_str = request.form.get("distance")
        distance = float(distance_str) if distance_str else None
        parks = request.form.getlist("parks")
        categories = request.form.getlist("categories")
        age_groups_input = request.form.getlist("age_groups")
        open_spots = request.form.get("open_spots", 1)
        lat = request.form.get("user_lat", type=float)
        lon = request.form.get("user_lon", type=float)
        
        scraper = ActivityScraper(
            distance_miles=distance,
            parks=parks,
            categories=categories,
            age_groups=age_groups_input,
            open_spots=open_spots,
            location = (lat, lon)
        )
        scraper.get_activities()

        session["activities"] = scraper.activities
        return redirect(url_for("results"))

    return render_template(INDEX_PATH,
                       parks=parks,
                       activity_names=activity_names,
                       age_groups=age_groups,
                       open_spots=open_spots)


@app.route("/results")
def results():
    activities = session.get("activities", [])
    activity_parks = get_activity_parks(activities)
    return render_template(RESULTS_PATH, activities=activities, activity_parks=activity_parks)


if __name__ == "__main__":
    app.run(debug=True)
