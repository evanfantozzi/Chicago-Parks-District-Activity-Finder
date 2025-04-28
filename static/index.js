// --- GLOBAL STATE ---
const AppState = {
    map: null,  // The Leaflet map object
    userLocationMarker: null,  // Marker for the user's location
    mapMarkers: [],  // Array to hold park markers on the map
    allParks: [],  // List of all parks
    userLatLng: null  // User's latitude and longitude
};

// --- MAP MANAGEMENT ---
const MapManager = {
    // Initializes the map and adds the base tile layer
    init() {
        AppState.map = L.map("map").setView([41.8781, -87.6298], 11.5);  // Set initial map center and zoom level
        L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png", {
            attribution: '&copy; OpenStreetMap & contributors, &copy; CARTO', // Attribution for map tiles
            subdomains: "abcd",  // Subdomains for map tiles
            maxZoom: 19  // Maximum zoom level
        }).addTo(AppState.map);  // Add the tile layer to the map
    },

    // Adds a user location marker to the map
    addUserMarker(latlng) {
        if (AppState.userLocationMarker) {
            AppState.map.removeLayer(AppState.userLocationMarker); // Remove existing marker if it exists
        }
        AppState.userLocationMarker = L.marker(latlng, {
            icon: L.icon({
                iconUrl: "https://maps.gstatic.com/mapfiles/api-3/images/spotlight-poi2_hdpi.png",  // Icon for user's location
                iconSize: [27, 43],  // Size of the icon
                iconAnchor: [13, 41],  // Anchor position of the icon
                popupAnchor: [0, -36]  // Popup anchor
            })
        }).addTo(AppState.map).bindPopup("You are here").openPopup();  // Add marker and popup for "You are here"
    },

    // Renders park markers on the map
    renderMarkers(parks) {
        AppState.mapMarkers.forEach(m => m.remove());  // Remove existing markers from the map
        AppState.mapMarkers = parks.map(p => L.marker([p.latitude, p.longitude]).addTo(AppState.map).bindPopup(p.name));  // Add new markers for parks
    },

    // Centers the map view based on the parks' locations
    centerView(parks) {
        const bounds = parks.map(p => [p.latitude, p.longitude]);  // Get the latitude and longitude of the parks
        if (AppState.userLocationMarker) bounds.push(AppState.userLocationMarker.getLatLng());  // Add user location marker if it exists
        if (bounds.length) AppState.map.fitBounds(bounds, {padding: [35, 35]});  // Fit the map to include all markers
        else AppState.map.setView([41.8781, -87.6298], 11.5);  // Default map view if no parks are available
    },

    // Clears all markers from the map
    clear() {
        AppState.mapMarkers.forEach(m => m.remove());  // Remove all markers
        AppState.mapMarkers = [];  // Reset the array of markers
    }
};

// --- PARK SELECTION ---
const ParkSelector = {
    // Haversine formula to calculate the distance between two lat/lon points
    haversine([lat1, lon1], [lat2, lon2]) {
        const toRad = x => x * Math.PI / 180;  // Converts degrees to radians
        const dLat = toRad(lat2 - lat1);  // Latitude difference
        const dLon = toRad(lon2 - lon1);  // Longitude difference
        const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;  // Haversine formula
        return 3958.8 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));  // Distance in miles
    },

    // Populates the park dropdown with checkboxes
    populateDropdown() {
        const dropdown = document.getElementById("parks-dropdown");  // Get the dropdown element
        dropdown.querySelectorAll("label").forEach(l => l.remove());  // Remove existing labels
        const parks = [...AppState.allParks];  // Copy of all parks
      
        if (AppState.userLatLng) {
            // Sort parks by distance from the user's location
            parks.sort((a, b) => this.haversine(AppState.userLatLng, [a.latitude, a.longitude]) - this.haversine(AppState.userLatLng, [b.latitude, b.longitude]));
        } else {
            // Sort parks alphabetically if no user location
            parks.sort((a, b) => a.name.localeCompare(b.name));
        }
      
        parks.forEach(p => {
            const label = document.createElement("label");  // Create a label for each park
            const cb = document.createElement("input");  // Create a checkbox for each park
            cb.type = "checkbox";  // Set checkbox type
            cb.name = "parks";  // Set checkbox name
            cb.value = p.name;  // Set checkbox value
            cb.addEventListener("change", ParkSelector.updateSelection);  // Add change listener for checkbox

            // Display distance if user location is available
            const dist = AppState.userLatLng
                ? ` (${ParkSelector.haversine(AppState.userLatLng, [p.latitude, p.longitude]).toFixed(1)} mi)`
                : "";
      
            label.append(cb, document.createTextNode(` ${p.name}${dist}`));  // Append checkbox and text
            dropdown.appendChild(label);  // Add label to the dropdown
        });
    },

    // Updates the selected parks on the map based on the checkboxes
    updateSelection() {
        const selected = Array.from(document.querySelectorAll('input[name="parks"]:checked')).map(cb => cb.value.trim().toLowerCase());  // Get selected parks
        const matched = AppState.allParks.filter(p => selected.includes(p.name.trim().toLowerCase()));  // Find matching parks
        MapManager.renderMarkers(matched);  // Render the markers for the selected parks
        MapManager.centerView(matched);  // Adjust the map view
        document.getElementById("clear-parks-btn").style.display = matched.length ? "block" : "none";  // Show/hide the "Clear Selection" button
        FilterManager.updateSummary();  // Update the filter summary
    },

    // Clears all selected parks
    clearSelection() {
        document.querySelectorAll('input[name="parks"]').forEach(cb => cb.checked = false);  // Uncheck all checkboxes
        MapManager.clear();  // Clear the map markers
        document.getElementById("clear-parks-btn").style.display = "none";  // Hide the "Clear Selection" button
        FilterManager.updateSummary();  // Update the filter summary
    }
};

// --- FILTER MANAGEMENT ---
const FilterManager = {
    // Updates the filter summary with selected categories and age groups
    updateSummary() {
        const summary = [];
      
        const anyCategories = document.getElementById("any_categories");  // "Any" category checkbox
        const cats = [...document.querySelectorAll('input[name="categories"]:checked')].map(cb => cb.parentElement.textContent.trim());  // Get selected categories
      
        if (cats.length === 0) {
            anyCategories.checked = true;  // Mark "Any" category as selected if no categories chosen
            summary.push("<li><strong>Activities:</strong> Any</li>");
        } else {
            anyCategories.checked = false;
            summary.push(`<li><strong>Activities:</strong> ${cats.join(", ")}</li>`);
        }
      
        const anyAgeGroups = document.getElementById("any_age_groups");  // "Any" age group checkbox
        const ages = [...document.querySelectorAll('input[name="age_groups"]:checked')].map(cb => cb.parentElement.textContent.trim());  // Get selected age groups
      
        if (ages.length === 0) {
            anyAgeGroups.checked = true;  // Mark "Any" age group as selected if no age groups chosen
            summary.push("<li><strong>Age Groups:</strong> Any</li>");
        } else {
            anyAgeGroups.checked = false;
            summary.push(`<li><strong>Age Groups:</strong> ${ages.join(", ")}</li>`);
        }
      
        summary.push("<li><strong>Parks/Facilities:</strong></li>");
        document.getElementById("form-summary").innerHTML = `<ul style="margin:0;padding-left:1rem;">${summary.join("")}</ul>`;  // Display the filter summary
    },

    // Updates the toggle state for each category group
    updateGroupToggles() {
        document.querySelectorAll(".group-toggle").forEach(toggle => {
            const group = toggle.dataset.group;  // Get the group from the toggle's data attribute
            const groupCheckboxes = document.querySelectorAll(`input[name="categories"][data-group="${group}"]`);  // Get checkboxes for that group
            const checkedCount = [...groupCheckboxes].filter(cb => cb.checked).length;  // Count checked checkboxes
      
            if (checkedCount === groupCheckboxes.length) {
                toggle.checked = true;  // If all checkboxes are checked, set toggle to checked
                toggle.indeterminate = false;
            } else if (checkedCount > 0) {
                toggle.checked = false;
                toggle.indeterminate = true;  // If some are checked, set toggle to indeterminate
            } else {
                toggle.checked = false;
                toggle.indeterminate = false;
            }
        });
    },

    // Enforces the "Any" checkbox behavior (if selected, uncheck all others)
    enforceAnyCheckboxes() {
        ["categories", "age_groups"].forEach(group => {
            const anyCheckbox = document.getElementById(`any_${group}`);  // "Any" checkbox for group
            const groupCheckboxes = document.querySelectorAll(`input[name="${group}"]`);  // Get all checkboxes in the group
      
            anyCheckbox.addEventListener("change", () => {
                if (anyCheckbox.checked) {
                    groupCheckboxes.forEach(cb => cb.checked = false);  // Uncheck all checkboxes if "Any" is selected
                }
      
                FilterManager.updateGroupToggles();  // Update the toggles
                FilterManager.updateSummary();  // Update the filter summary
            });
      
            groupCheckboxes.forEach(cb => {
                cb.addEventListener("change", () => {
                    if (cb.checked) anyCheckbox.checked = false;  // If any checkbox is selected, uncheck "Any"
                    FilterManager.updateSummary();  // Update the filter summary
                });
            });
        });
    },

    // Sets up group toggle functionality
    setupGroupToggles() {
        document.querySelectorAll(".group-toggle").forEach(toggle => {
            toggle.addEventListener("change", (e) => {
                const group = e.target.dataset.group;  // Get the group from the toggle's data attribute
                const checkboxes = document.querySelectorAll(`input[name="categories"][data-group="${group}"]`);  // Get all checkboxes in the group
            
                checkboxes.forEach(cb => {
                    cb.checked = toggle.checked;  // Check/uncheck the child activities
                });

                document.getElementById("any_categories").checked = false;  // Uncheck "any" checkbox for categories
                FilterManager.updateGroupToggles();  // Update the group toggles
                FilterManager.updateSummary();  // Update the filter summary
            });
        });
      
        // Individual activities
        document.querySelectorAll('input[name="categories"]').forEach(cb => {
            cb.addEventListener("change", () => {
                FilterManager.updateGroupToggles();  // Update the group toggles when an individual activity is changed
                FilterManager.updateSummary();  // Update the filter summary
            });
        });
    }
};

// --- NEARBY PARKS --- 
const NearbyParks = {
    // Updates the label for the nearby parks button based on selected distance
    updateButtonLabel() {
        const val = document.getElementById("distance").value.trim();  // Get the value of the distance input
        document.getElementById("nearby-btn").textContent = val ? `Look For Locations Within ${val} Miles` : "Get Locations";  // Update the button text based on the distance value
    },

    // Loads nearby parks based on user location and selected distance
    loadNearby() {
        const radius = parseFloat(document.getElementById("distance").value || "2");  // Get the radius from the input (default to 2 miles if empty)
        if (!AppState.userLatLng) return;  // Return if user location is not available
  
        document.querySelectorAll('input[name="parks"]').forEach(cb => {
            const park = AppState.allParks.find(p => p.name.trim().toLowerCase() === cb.value.trim().toLowerCase());  // Find park based on checkbox value
            if (!park) return;
            const dist = ParkSelector.haversine(AppState.userLatLng, [park.latitude, park.longitude]);  // Calculate the distance from user location
            cb.checked = dist <= radius;  // Check the checkbox if the park is within the radius
        });
        MapManager.addUserMarker(AppState.userLatLng);  // Add user location marker
        ParkSelector.updateSelection();  // Update the park selection
    }
};

// --- DROPDOWN MANAGEMENT ---
const DropdownManager = {
    // Sets up the dropdown toggle functionality
    setup() {
        document.querySelectorAll(".dropdown-toggle").forEach(btn => {
            btn.addEventListener("click", () => btn.closest(".dropdown-checkbox").classList.toggle("open"));
        });

        // Filter dropdown items as the user types
        document.querySelectorAll(".dropdown-search").forEach(input => {
            input.addEventListener("input", () => {
                const filter = input.value.toLowerCase();
                const dropdown = input.closest(".dropdown-checkbox").querySelector(".dropdown-content");

                let currentGroup = null;
                let groupHasMatch = false;

                dropdown.querySelectorAll(".dropdown-group, label").forEach(el => {
                    if (el.classList.contains("dropdown-group")) {
                        if (currentGroup && !groupHasMatch) {
                            currentGroup.style.display = "none";
                        }
                        currentGroup = el;
                        groupHasMatch = false;
                        el.style.display = "none";
                    } else {
                        const match = el.textContent.toLowerCase().includes(filter);
                        el.style.display = match ? "block" : "none";
                        if (match && currentGroup) {
                            groupHasMatch = true;
                            currentGroup.style.display = "block";
                        }
                    }
                });

                if (currentGroup && !groupHasMatch) {
                    currentGroup.style.display = "none";
                }
            });

            // Prevent Enter key from submitting form
            input.addEventListener("keydown", e => {
                if (e.key === "Enter") {
                    e.preventDefault();
                }
            });
        });

        document.addEventListener("click", e => {
            let closed = false;
            document.querySelectorAll(".dropdown-checkbox.open").forEach(dd => {
                if (!dd.contains(e.target)) {
                    dd.classList.remove("open");
                    closed = true;
                }
            });

            if (closed) {
                FilterManager.updateGroupToggles();
                FilterManager.updateSummary();
            }
        });
    }
};


// --- DOM READY ---
document.addEventListener("DOMContentLoaded", () => {
    AppState.allParks = window.allParks || [];  // Initialize parks data
    MapManager.init();  // Initialize the map
    FilterManager.enforceAnyCheckboxes();  // Enforce the "Any" checkbox behavior
    FilterManager.setupGroupToggles();  // Set up the group toggles for categories
    DropdownManager.setup();  // Set up the dropdown functionality

    // Event listener for the distance input to update the button label
    document.getElementById("distance").addEventListener("input", () => {
        NearbyParks.updateButtonLabel();
        FilterManager.updateSummary();
        FilterManager.updateGroupToggles();
    });

    // Event listener for clearing park selections
    document.getElementById("clear-parks-btn").addEventListener("click", ParkSelector.clearSelection);

    // Prevent form submission if no parks or distance is selected
    document.querySelector("form").addEventListener("submit", e => {
        const hasDistance = document.getElementById("distance").value.trim();
        const hasParks = document.querySelectorAll('input[name="parks"]:checked').length;
        if (!hasDistance && !hasParks) {
            e.preventDefault();
            document.getElementById("form-summary").innerHTML = `<span style="color: red; font-weight: bold;">Please enter a distance or select at least one park before submitting.</span>`;
        }
    });

    // Get user's geolocation and initialize map and parks
    navigator.geolocation.getCurrentPosition(
        pos => {
            // Successfully got user location
            AppState.userLatLng = [pos.coords.latitude, pos.coords.longitude];
            document.getElementById("user-lat").value = pos.coords.latitude;
            document.getElementById("user-lon").value = pos.coords.longitude;
    
            ParkSelector.populateDropdown(); // Populate dropdown sorted by distance
            MapManager.addUserMarker(AppState.userLatLng); // Add "You are here" marker
            NearbyParks.loadNearby(); // Auto-check parks within distance
        },
        err => {
            // Failed to get user location (user denied, blocked, or error)
            console.warn("Geolocation failed, falling back to alphabetical park list:", err);
    
            ParkSelector.populateDropdown(); // Populate parks alphabetically
        }
    );
    
});
