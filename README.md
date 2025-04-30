## Welcome to *Chicago Activity Finder!*

I built this web app after a friend relayed their frustrations with the various existing Chicago Park District pages that [don't show availability](https://data.cityofchicago.org/stories/s/Chicago-Park-District-Activities-Search/gthm-mv9y), [don't allow easy searching](https://www.chicagoparkdistrict.com/events/map?), and [use poor formatting](https://data.cityofchicago.org/stories/s/Chicago-Park-District-Activities-Search/gthm-mv9y).


This web app started from a simple idea: finding city-run activities shouldn't be so hard. I built this project to help Chicago residents easily explore free and low-cost programming near them — without fighting a clunky government website.

With that in mind, the app lets you:

- 🧭 **Search by location** — use your current location or manually enter any Chicago address  
- 🧒 **Filter by age group** — from toddler play to senior fitness, there’s something for everyone  
- 🧘 **Choose activity types** — like dance, nature, sports, arts, and more  
- 🏞️ **Pick nearby parks** — either by distance or by browsing a full list  
- 🗺️ **See it all on an interactive map** — complete with clickable markers and “You are here”  

The app scrapes **real-time activity listings** directly from the Chicago Park District and groups multiple session times into a single, clean card. You can scroll, search, and even load more results — all without reloading the page.

---

I built this using **Flask**, **Leaflet**, and a spatial SQLite database to support distance-based park search. The scraper runs on the Chicago Park District’s internal API, and the whole frontend is styled with a responsive, mobile-first layout.

Want to try it out? [Check out the live version here](#)  
Spotted a bug or weird result? [Open an issue](https://github.com/evanfantozzi) or shoot me a message.
