// New, cleaner index.js

// --- GLOBAL STATE ---
const AppState = {
    map: null,
    userLocationMarker: null,
    mapMarkers: [],
    allParks: [],
    userLatLng: null
  };
  
  // --- MAP MANAGEMENT ---
  const MapManager = {
    init() {
      AppState.map = L.map("map").setView([41.8781, -87.6298], 11.5);
      L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png", {
        attribution: '&copy; OpenStreetMap & contributors, &copy; CARTO',
        subdomains: "abcd",
        maxZoom: 19
      }).addTo(AppState.map);
    },
  
    addUserMarker(latlng) {
      if (AppState.userLocationMarker) {
        AppState.map.removeLayer(AppState.userLocationMarker);
      }
      AppState.userLocationMarker = L.marker(latlng, {
        icon: L.icon({
          iconUrl: "https://maps.gstatic.com/mapfiles/api-3/images/spotlight-poi2_hdpi.png",
          iconSize: [27, 43],
          iconAnchor: [13, 41],
          popupAnchor: [0, -36]
        })
      }).addTo(AppState.map).bindPopup("You are here").openPopup();
    },
  
    renderMarkers(parks) {
      AppState.mapMarkers.forEach(m => m.remove());
      AppState.mapMarkers = parks.map(p => L.marker([p.latitude, p.longitude]).addTo(AppState.map).bindPopup(p.name));
    },
  
    centerView(parks) {
      const bounds = parks.map(p => [p.latitude, p.longitude]);
      if (AppState.userLocationMarker) bounds.push(AppState.userLocationMarker.getLatLng());
      if (bounds.length) AppState.map.fitBounds(bounds, {padding: [35, 35]});
      else AppState.map.setView([41.8781, -87.6298], 11.5);
    },
  
    clear() {
        AppState.mapMarkers.forEach(m => m.remove());
        AppState.mapMarkers = []; 
    }
      
  };
  
  // --- PARK SELECTION ---
  const ParkSelector = {
    haversine([lat1, lon1], [lat2, lon2]) {
      const toRad = x => x * Math.PI / 180;
      const dLat = toRad(lat2 - lat1);
      const dLon = toRad(lon2 - lon1);
      const a = Math.sin(dLat/2)**2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon/2)**2;
      return 3958.8 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    },
  
    populateDropdown() {
        const dropdown = document.getElementById("parks-dropdown");
        dropdown.querySelectorAll("label").forEach(l => l.remove());
        const parks = [...AppState.allParks];
      
        if (AppState.userLatLng) {
          parks.sort((a, b) => this.haversine(AppState.userLatLng, [a.latitude, a.longitude]) - this.haversine(AppState.userLatLng, [b.latitude, b.longitude]));
        } else {
          parks.sort((a, b) => a.name.localeCompare(b.name));
        }
      
        parks.forEach(p => {
          const label = document.createElement("label");
          const cb = document.createElement("input");
          cb.type = "checkbox";
          cb.name = "parks";
          cb.value = p.name;
          cb.addEventListener("change", ParkSelector.updateSelection);
      
          const dist = AppState.userLatLng
            ? ` (${ParkSelector.haversine(AppState.userLatLng, [p.latitude, p.longitude]).toFixed(1)} mi)`
            : "";
      
          label.append(cb, document.createTextNode(` ${p.name}${dist}`));
          dropdown.appendChild(label);
        });
      },
  
    updateSelection() {
      const selected = Array.from(document.querySelectorAll('input[name="parks"]:checked')).map(cb => cb.value.trim().toLowerCase());
      const matched = AppState.allParks.filter(p => selected.includes(p.name.trim().toLowerCase()));
      MapManager.renderMarkers(matched);
      MapManager.centerView(matched);
      document.getElementById("clear-parks-btn").style.display = matched.length ? "block" : "none";
      FilterManager.updateSummary();
    },
  
    clearSelection() {
      document.querySelectorAll('input[name="parks"]').forEach(cb => cb.checked = false);
      MapManager.clear();
      document.getElementById("clear-parks-btn").style.display = "none";
      FilterManager.updateSummary();
    }
  };
  
  // --- FILTER MANAGEMENT ---
  const FilterManager = {
    updateSummary() {
        const summary = [];
      
        const anyCategories = document.getElementById("any_categories");
        const cats = [...document.querySelectorAll('input[name="categories"]:checked')].map(cb => cb.parentElement.textContent.trim());
      
        if (cats.length === 0) {
          anyCategories.checked = true;
          summary.push("<li><strong>Activities:</strong> Any</li>");
        } else {
          anyCategories.checked = false;
          summary.push(`<li><strong>Activities:</strong> ${cats.join(", ")}</li>`);
        }
      
        const anyAgeGroups = document.getElementById("any_age_groups");
        const ages = [...document.querySelectorAll('input[name="age_groups"]:checked')].map(cb => cb.parentElement.textContent.trim());
      
        if (ages.length === 0) {
          anyAgeGroups.checked = true;
          summary.push("<li><strong>Age Groups:</strong> Any</li>");
        } else {
          anyAgeGroups.checked = false;
          summary.push(`<li><strong>Age Groups:</strong> ${ages.join(", ")}</li>`);
        }
      
        summary.push("<li><strong>Parks/Facilities:</strong></li>");
        document.getElementById("form-summary").innerHTML = `<ul style="margin:0;padding-left:1rem;">${summary.join("")}</ul>`;
      },

    updateGroupToggles() {
        document.querySelectorAll(".group-toggle").forEach(toggle => {
          const group = toggle.dataset.group;
          const groupCheckboxes = document.querySelectorAll(`input[name="categories"][data-group="${group}"]`);
          const checkedCount = [...groupCheckboxes].filter(cb => cb.checked).length;
      
          if (checkedCount === groupCheckboxes.length) {
            toggle.checked = true;
            toggle.indeterminate = false;
          } else if (checkedCount > 0) {
            toggle.checked = false;
            toggle.indeterminate = true;
          } else {
            toggle.checked = false;
            toggle.indeterminate = false;
          }
        });
    },
  
    enforceAnyCheckboxes() {
        ["categories", "age_groups"].forEach(group => {
          const anyCheckbox = document.getElementById(`any_${group}`);
          const groupCheckboxes = document.querySelectorAll(`input[name="${group}"]`);
      
          anyCheckbox.addEventListener("change", () => {
            if (anyCheckbox.checked) {
              groupCheckboxes.forEach(cb => cb.checked = false);
      
              if (group === "categories") {
                document.querySelectorAll(".group-toggle").forEach(toggle => {
                  toggle.checked = false;
                  toggle.indeterminate = false;
                });
              }
      
              FilterManager.updateGroupToggles();
              FilterManager.updateSummary();
            }
          });
      
          groupCheckboxes.forEach(cb => {
            cb.addEventListener("change", () => {
              if (cb.checked) anyCheckbox.checked = false;
              FilterManager.updateSummary();
            });
          });
        });
    },    
  
    setupGroupToggles() {
        // Group toggles (like "Sports" or "Arts")
        document.querySelectorAll(".group-toggle").forEach(toggle => {
          toggle.addEventListener("change", (e) => {
            const group = e.target.dataset.group;
            const checkboxes = document.querySelectorAll(`input[name="categories"][data-group="${group}"]`);
            
            checkboxes.forEach(cb => {
              cb.checked = toggle.checked;  // check/uncheck the child activities
            });

            document.getElementById("any_categories").checked = false; // Uncheck "any"
      
            FilterManager.updateGroupToggles();  // update the toggle indeterminate/checked states
            FilterManager.updateSummary();       // update the summary of selected activities
          });
        });
      
        // Individual activities
        document.querySelectorAll('input[name="categories"]').forEach(cb => {
          cb.addEventListener("change", () => {
            FilterManager.updateGroupToggles();
            FilterManager.updateSummary();
          });
        });
      }
    }      
  
  // --- NEARBY PARKS ---
  const NearbyParks = {
    updateButtonLabel() {
      const val = document.getElementById("distance").value.trim();
      document.getElementById("nearby-btn").textContent = val ? `Look For Locations Within ${val} Miles` : "Get Locations";
    },
  
    loadNearby() {
      const radius = parseFloat(document.getElementById("distance").value || "2");
      if (!AppState.userLatLng) return;
  
      document.querySelectorAll('input[name="parks"]').forEach(cb => {
        const park = AppState.allParks.find(p => p.name.trim().toLowerCase() === cb.value.trim().toLowerCase());
        if (!park) return;
        const dist = ParkSelector.haversine(AppState.userLatLng, [park.latitude, park.longitude]);
        cb.checked = dist <= radius;
      });
      MapManager.addUserMarker(AppState.userLatLng);
      ParkSelector.updateSelection();

      
    }
  };
  
  // --- DROPDOWN MANAGEMENT ---
  const DropdownManager = {
    setup() {
      document.querySelectorAll(".dropdown-toggle").forEach(btn => {
        btn.addEventListener("click", () => btn.closest(".dropdown-checkbox").classList.toggle("open"));
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
    AppState.allParks = window.allParks || [];
    MapManager.init();
    FilterManager.enforceAnyCheckboxes();
    FilterManager.setupGroupToggles();
    DropdownManager.setup();
  
    document.getElementById("distance").addEventListener("input", () => {
      NearbyParks.updateButtonLabel();
      FilterManager.updateSummary();
      FilterManager.updateGroupToggles();
    });
  
    document.getElementById("clear-parks-btn").addEventListener("click", ParkSelector.clearSelection);
  
    document.querySelector("form").addEventListener("submit", e => {
      const hasDistance = document.getElementById("distance").value.trim();
      const hasParks = document.querySelectorAll('input[name="parks"]:checked').length;
      if (!hasDistance && !hasParks) {
        e.preventDefault();
        document.getElementById("form-summary").innerHTML = `<span style="color: red; font-weight: bold;">Please enter a distance or select at least one park before submitting.</span>`;
      }
    });
  
    navigator.geolocation.getCurrentPosition(pos => {
      AppState.userLatLng = [pos.coords.latitude, pos.coords.longitude];
      document.getElementById("user-lat").value = pos.coords.latitude;
      document.getElementById("user-lon").value = pos.coords.longitude;
  
      ParkSelector.populateDropdown();
      MapManager.addUserMarker(AppState.userLatLng);
      NearbyParks.loadNearby();
    });
  });