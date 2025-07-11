## 🌳 Welcome to the improved *Chicago Parks District Activity Finder!*

Did you know the Chicago Park District offers tons of amazing events year-round? Unfortunately, they can be surprisingly hard to find. A friend of mine shared their frustration with the existing Park District websites, which [don't allow distance-based searches](https://anc.apm.activecommunities.com/chicagoparkdistrict/activity/search?) and are hard to navigate through.

This web app started from the idea that finding public events with availability should be quick and seamless. My hope is that it helps my friends — and other Chicago residents — more easily explore free and low-cost programming across the city.

With that in mind, the app lets you:

- **Search for activities by proximity** — use your current location or manually enter any Chicago address. You can also add or remove individual parks/facilities from the list of searched areas.
- **Filter by age group and activity type** — to narrow your results based on what matters to you.
- **Fetch real-time available listings** — pulled directly from the Chicago Park District, with multiple sessions grouped into single, clean listings.
- **View everything on an interactive map** — complete with clickable markers, activity popups, and direct registration links.

---

I built this using **Flask**, **Leaflet**, and a spatial SQLite database to support distance-based queries. The app's scraper interacts with the Park District’s internal API, and the frontend is styled to work cleanly across both desktop and mobile.

Want to try it out? [Check out the live version here](https://www.chicagoactivities.onrender.com)

![Demo GIF](static/read_me.gif)

Find a bug? [Shoot me a message](mailto:evanfantozzi@uchicago.edu).
