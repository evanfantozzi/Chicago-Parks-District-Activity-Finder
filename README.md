## 🌳 Welcome to *Chicago Activity Finder!*

Did you know the Chicago Park District offers tons of amazing events year-round? Unfortunately, they can be surprisingly hard to find. A friend of mine shared their frustration with the existing Park District websites — some [don’t show whether events still have spots left](https://data.cityofchicago.org/stories/s/Chicago-Park-District-Activities-Search/gthm-mv9y), others [make it difficult to search](https://www.chicagoparkdistrict.com/events/map?), and many [suffer from poor formatting](https://data.cityofchicago.org/stories/s/Chicago-Park-District-Activities-Search/gthm-mv9y).

This web app started from the idea that finding public events with availability should be quick and seamless. My hope is that it my friends and other Chicago residents more easily explore free and low-cost activities.

With that in mind, the app lets you:

- **Search for activities by proximity** using your current location or manually enter any Chicago address if you're far away or have your location sharing off. You can also manually add/remove parks/facilities from the list of searched areas
- **Filter by age group and activity types** to narrow down on the most important filters - what do you want to do?  
- **Fetch real-time available activity listings** - from the Chicago Park District based on your search query, consolidating multiple listings of the same event with different session times. 
- **See it all on an interactive map** — complete with clickable markers, allowing you to easily see your activity options and navigate to registration links when needed. 

---

I built this using **Flask**, **Leaflet**, and a spatial SQLite database to support distance-based park search. The scraper runs on the Chicago Park District’s internal API, and the whole frontend is styled with a responsive, mobile-first layout.

Want to try it out? [Check out the live version here](https://www.chicagoactivities.onrender.com)  
Find a bug? [shoot me a message](https://github.com/evanfantozzi).
