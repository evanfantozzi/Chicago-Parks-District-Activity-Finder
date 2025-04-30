// --- GLOBAL STATE ---
const AppState = {
    map: null, // Leaflet map 
    userLocationMarker: null, // Marker for user's location
    mapMarkers: [], // List to hold park markers
    allParks: [], // List of all parks
    userLatLng: null // User's latitude and longitude
};

// Helper function to get checked values of checkboxes
function getCheckedValues(name) {
    return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`)).map(cb => cb.value.trim().toLowerCase());
}

// Helper function - Haversine formula to calculate distance between two points (lat, lon)
function haversineDistance([lat1, lon1], [lat2, lon2]) {
    const toRad = x => x * Math.PI / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
    return 3958.8 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)); // Returns distance in miles
}

// Function to disable autocomplete on geosearch input field
function disableAutocompleteOnGeoSearch() {
    setTimeout(() => {
        const input = document.querySelector('.leaflet-control.geosearch input');
        if (input) {
            Object.assign(input, {
                autocomplete: 'off',
                autocorrect: 'off',
                autocapitalize: 'off',
                spellcheck: false,
                type: 'search',
                name: 'geo-address'
            });
        }
    }, 500);
}

// MapManager handles map-related functions
const MapManager = {
    init() {
        // Initialize the map and set default view
        AppState.map = L.map("map").setView([41.8781, -87.6298], 11.5);
        
        // Add tile layer (OpenStreetMap)
        L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png", {
            attribution: '&copy; OpenStreetMap & contributors, &copy; CARTO',
            subdomains: "abcd",
            maxZoom: 19
        }).addTo(AppState.map);

        // Show geosearch if user location is undefined or far from default location
        const showSearch = !AppState.userLatLng || haversineDistance(AppState.userLatLng, [41.8781, -87.6298]) > 75;

        if (showSearch) {
            const provider = new window.GeoSearch.OpenStreetMapProvider({
                params: { viewbox: '-91.5, 42.5, -87, 37', bounded: 1 }
            });

            const search = new window.GeoSearch.GeoSearchControl({
                provider,
                style: 'bar',
                position: 'bottomleft',
                autoComplete: true,
                autoCompleteDelay: 250,
                showMarker: false,
                marker: false,
                showPopup: true,
                retainZoomLevel: false,
                animateZoom: true,
                searchLabel: 'Enter Location Here'
            });

            AppState.map.addControl(search); // Add geosearch control to map
            disableAutocompleteOnGeoSearch(); // Disable autocomplete for geosearch

            //  Flash effect to search input box once it's displayed
            setTimeout(() => {
                const searchBox = document.querySelector('.leaflet-control-geosearch input');
                if (searchBox) {
                    searchBox.classList.add('flashBox'); // Apply flashing class to search input
                }
            }, 500); // Apply after 500ms to ensure the search box is loaded
            
            // Event listener for geosearch location select
            AppState.map.on('geosearch/showlocation', ({ location }) => {
                if (!location.label.toLowerCase().includes("illinois")) {
                    alert("Please select a location within Illinois."); // Location validation
                    return;
                }
                const { x, y } = location;
                AppState.userLatLng = [y, x];
                document.getElementById("user-lat").value = y;
                document.getElementById("user-lon").value = x;

                ParkSelector.populateDropdown(); // Populate park dropdown based on new location
                MapManager.addUserMarker(AppState.userLatLng); // Add user location marker
                NearbyParks.loadNearby(); // Load nearby parks
            });
        }
    },

    // Add user marker on the map
    addUserMarker(latlng) {
        if (AppState.userLocationMarker) {
            AppState.map.removeLayer(AppState.userLocationMarker); // Remove previous marker if exists
        }
        AppState.userLocationMarker = L.marker(latlng, {
            icon: L.icon({
                iconUrl: "https://maps.gstatic.com/mapfiles/api-3/images/spotlight-poi2_hdpi.png",
                iconSize: [27, 43],
                iconAnchor: [13, 41],
                popupAnchor: [0, -36]
            })
        }).addTo(AppState.map).bindPopup("You are here").openPopup(); // Bind a popup to the marker

        AppState.map.flyTo(latlng, 13); // Fly to user's location on the map
    },

    // Render park markers on the map
    renderMarkers(parks) {
        AppState.mapMarkers.forEach(m => m.remove()); // Remove existing markers
        AppState.mapMarkers = parks.map(p =>
            L.marker([p.latitude, p.longitude]).addTo(AppState.map).bindPopup(p.name) // Add new markers
        );
    },

    // Center the map on the parks' bounding box
    centerView(parks) {
        const bounds = parks.map(p => [p.latitude, p.longitude]);
        if (AppState.userLocationMarker) bounds.push(AppState.userLocationMarker.getLatLng());
        bounds.length ? AppState.map.fitBounds(bounds, { padding: [35, 35] }) : AppState.map.setView([41.8781, -87.6298], 11.5); // Fit map to bounds
    },

    // Clear all markers from the map
    clear() {
        AppState.mapMarkers.forEach(m => m.remove());
        AppState.mapMarkers = []; // Reset mapMarkers array
    }
};

// ParkSelector handles the park selection functionality
const ParkSelector = {
    populateDropdown() {
        const dropdown = document.getElementById("parks-dropdown");
        dropdown.querySelectorAll("label").forEach(l => l.remove()); // Clear previous dropdown labels

        const parks = [...AppState.allParks];
        // Sort parks either by distance from user or alphabetically
        parks.sort((a, b) => AppState.userLatLng
            ? haversineDistance(AppState.userLatLng, [a.latitude, a.longitude]) - haversineDistance(AppState.userLatLng, [b.latitude, b.longitude])
            : a.name.localeCompare(b.name));

        parks.forEach(p => {
            const label = document.createElement("label");
            const cb = Object.assign(document.createElement("input"), {
                type: "checkbox",
                name: "parks",
                value: p.name
            });
            cb.addEventListener("change", this.updateSelection); // Add event listener for checkbox change

            // Show distance from user if user location is available
            const dist = AppState.userLatLng ? ` (${haversineDistance(AppState.userLatLng, [p.latitude, p.longitude]).toFixed(1)} mi)` : "";
            label.append(cb, ` ${p.name}${dist}`);
            dropdown.appendChild(label);
        });
    },

    // Update park selection based on checkbox status
    updateSelection() {
        const selected = getCheckedValues("parks");
        const matched = AppState.allParks.filter(p => selected.includes(p.name.trim().toLowerCase()));
        MapManager.renderMarkers(matched); // Render the selected parks on the map
        MapManager.centerView(matched); // Center the map on the selected parks
        document.getElementById("clear-parks-btn").style.display = matched.length ? "block" : "none"; // Show/hide clear button
        FilterManager.updateSummary(); // Update the summary with selected filters
    },

    // Clear all park selections
    clearSelection() {
        document.querySelectorAll('input[name="parks"]').forEach(cb => cb.checked = false); // Uncheck all checkboxes
        MapManager.clear(); // Clear markers
        document.getElementById("clear-parks-btn").style.display = "none"; // Hide clear button
        FilterManager.updateSummary(); // Update the summary
    }
};

// NearbyParks handles the functionality for showing nearby parks
const NearbyParks = {
    // Update the "Look For Locations" button label based on the distance
    updateButtonLabel() {
        const val = document.getElementById("distance").value.trim();
        document.getElementById("nearby-btn").textContent = val ? `Look For Locations Within ${val} Miles` : "Get Locations";
    },

    // Load nearby parks based on the distance entered
    loadNearby() {
        const radius = parseFloat(document.getElementById("distance").value || "2"); // Get the radius from input
        if (!AppState.userLatLng) return;

        document.querySelectorAll('input[name="parks"]').forEach(cb => {
            const park = AppState.allParks.find(p => p.name.trim().toLowerCase() === cb.value.trim().toLowerCase());
            if (!park) return;
            cb.checked = haversineDistance(AppState.userLatLng, [park.latitude, park.longitude]) <= radius; // Check park if within distance
        });

        MapManager.addUserMarker(AppState.userLatLng); // Add user location marker
        ParkSelector.updateSelection(); // Update park selection
    }
};

// FilterManager handles updating the filter summary
const FilterManager = {
    // Update the filter summary with selected categories and parks
    updateSummary() {
        const summary = [];

        const anyCategories = document.getElementById("any_categories");
        const cats = getCheckedValues("categories").map(v => {
            const cb = [...document.querySelectorAll('input[name="categories"]')].find(el => el.value.trim().toLowerCase() === v);
            return cb ? cb.parentElement.textContent.trim() : v;
        });

        if (cats.length === 0) {
            anyCategories.checked = true;
            summary.push("<li><strong>Activities:</strong> Any</li>");
        } else {
            anyCategories.checked = false;
            summary.push(`<li><strong>Activities:</strong> ${cats.join(", ")}</li>`);
        }

        const anyAgeGroups = document.getElementById("any_age_groups");
        const ages = getCheckedValues("age_groups").map(v => {
            const cb = [...document.querySelectorAll('input[name="age_groups"]')].find(el => el.value.trim().toLowerCase() === v);
            return cb ? cb.parentElement.textContent.trim() : v;
        });

        if (ages.length === 0) {
            anyAgeGroups.checked = true;
            summary.push("<li><strong>Age Groups:</strong> Any</li>");
        } else {
            anyAgeGroups.checked = false;
            summary.push(`<li><strong>Age Groups:</strong> ${ages.join(", ")}</li>`);
        }

        summary.push("<li><strong>Parks/Facilities:</strong></li>");
        document.getElementById("form-summary").innerHTML = `<ul style="margin:0;padding-left:1rem;">${summary.join("")}</ul>`; // Display summary
    },

    // Update the checkboxes for group toggles (e.g., select/deselect all in category)
    updateGroupToggles() {
        document.querySelectorAll(".group-toggle").forEach(toggle => {
            const group = toggle.dataset.group;
            const groupCheckboxes = document.querySelectorAll(`input[name="categories"][data-group="${group}"]`);
            const checkedCount = [...groupCheckboxes].filter(cb => cb.checked).length;

            toggle.checked = checkedCount === groupCheckboxes.length; // Check toggle if all are checked
            toggle.indeterminate = checkedCount > 0 && checkedCount < groupCheckboxes.length; // Indeterminate if some are checked
        });
    },

    // Enforce the behavior of the "Any" checkbox (deselect all other checkboxes if selected)
    enforceAnyCheckboxes() {
        ["categories", "age_groups"].forEach(group => {
            const anyCheckbox = document.getElementById(`any_${group}`);
            const groupCheckboxes = document.querySelectorAll(`input[name="${group}"]`);

            anyCheckbox.addEventListener("change", () => {
                if (anyCheckbox.checked) {
                    groupCheckboxes.forEach(cb => cb.checked = false); // Uncheck all group checkboxes
                }
                FilterManager.updateGroupToggles(); // Update group toggles
                FilterManager.updateSummary(); // Update summary
            });

            groupCheckboxes.forEach(cb => {
                cb.addEventListener("change", () => {
                    if (cb.checked) anyCheckbox.checked = false; // Uncheck "Any" if any checkbox is selected
                    FilterManager.updateSummary(); // Update summary
                });
            });
        });
    },

    // Set up event listeners for category group toggles
    setupGroupToggles() {
        document.querySelectorAll(".group-toggle").forEach(toggle => {
            toggle.addEventListener("change", e => {
                const group = e.target.dataset.group;
                const checkboxes = document.querySelectorAll(`input[name="categories"][data-group="${group}"]`);
                checkboxes.forEach(cb => cb.checked = toggle.checked); // Check/uncheck all checkboxes in group

                document.getElementById("any_categories").checked = false; // Uncheck "Any" checkbox
                FilterManager.updateGroupToggles(); // Update group toggles
                FilterManager.updateSummary(); // Update summary
            });
        });

        document.querySelectorAll('input[name="categories"]').forEach(cb => {
            cb.addEventListener("change", () => {
                FilterManager.updateGroupToggles(); // Update group toggles
                FilterManager.updateSummary(); // Update summary
            });
        });
    }
};

// DropdownManager handles dropdown UI interactions
const DropdownManager = {
    setup() {
        document.querySelectorAll(".dropdown-toggle").forEach(btn => {
            btn.addEventListener("click", () => btn.closest(".dropdown-checkbox").classList.toggle("open")); // Toggle dropdown open/close
        });

        document.querySelectorAll(".dropdown-search").forEach(input => {
            input.addEventListener("input", () => {
                const filter = input.value.toLowerCase();
                const dropdown = input.closest(".dropdown-checkbox").querySelector(".dropdown-content");

                dropdown.querySelectorAll(".dropdown-group").forEach(group => group.style.display = "none"); // Hide all groups
                dropdown.querySelectorAll("label").forEach(label => {
                    const match = label.textContent.toLowerCase().includes(filter); // Filter labels based on input
                    label.style.display = match ? "block" : "none";
                    if (match) {
                        const group = label.previousElementSibling;
                        if (group && group.classList.contains("dropdown-group")) {
                            group.style.display = "block"; // Show group if match found
                        }
                    }
                });
            });

            // Prevent Enter key from submitting the form
            input.addEventListener("keydown", e => {
                if (e.key === "Enter") e.preventDefault();
            });
        });

        // Close dropdown if clicked outside
        document.addEventListener("click", e => {
            let closed = false;
            document.querySelectorAll(".dropdown-checkbox.open").forEach(dd => {
                if (!dd.contains(e.target)) {
                    dd.classList.remove("open"); // Close dropdown
                    closed = true;
                }
            });
            if (closed) {
                FilterManager.updateGroupToggles(); // Update group toggles
                FilterManager.updateSummary(); // Update summary
            }
        });
    }
};

// Initialize everything when the document is ready
document.addEventListener("DOMContentLoaded", () => {
    AppState.allParks = window.allParks || []; // Initialize parks list

    navigator.geolocation.getCurrentPosition(
        pos => {
            AppState.userLatLng = [pos.coords.latitude, pos.coords.longitude];
            document.getElementById("user-lat").value = pos.coords.latitude;
            document.getElementById("user-lon").value = pos.coords.longitude;

            MapManager.init(); // Initialize the map
            ParkSelector.populateDropdown(); // Populate the parks dropdown
            MapManager.addUserMarker(AppState.userLatLng); // Add the user marker
            NearbyParks.loadNearby(); // Load nearby parks
            NearbyParks.updateButtonLabel(); // Update the button label
        },
        err => {
            console.warn("Geolocation failed:", err);
            MapManager.init(); // Initialize the map even if geolocation fails
            ParkSelector.populateDropdown(); // Populate the dropdown anyway
            FilterManager.updateSummary(); // Update summary
            NearbyParks.updateButtonLabel(); // Update button label
        }
    );

    FilterManager.enforceAnyCheckboxes(); // Enforce "Any" checkbox behavior
    FilterManager.setupGroupToggles(); // Set up category group toggles
    DropdownManager.setup(); // Set up dropdown interaction

    document.getElementById("distance").addEventListener("input", () => {
        NearbyParks.updateButtonLabel(); // Update button label when distance changes
        FilterManager.updateSummary(); // Update summary
        FilterManager.updateGroupToggles(); // Update group toggles
    });

    document.getElementById("clear-parks-btn").addEventListener("click", ParkSelector.clearSelection); // Clear parks selection
});
