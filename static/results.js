// Global variables
let map;
let parkMarkers = []; // Stores Leaflet markers
let activityCards = new Map(); // Maps place names to activity card DOM elements

// Get park data passed from the server into the page
const parkData = window.parkData;

// Render park markers on the map
function renderMapMarkers(parkData) {
  const bounds = [];

  parkData.forEach(([name, lat, lon, activities]) => {
    // Avoid adding duplicate markers
    const existingMarker = parkMarkers.find(marker => marker.placeName === name);
    if (existingMarker) return;

    const uniqueActivities = [...new Set(activities)];
    
    // Create a Leaflet marker
    const marker = L.marker([lat, lon])
      .addTo(map)
      .bindPopup(`<strong>${name}</strong><br>${uniqueActivities.map(a => `• ${a}`).join('<br>')}`)
      .on('click', () => openActivityCardByPlace(name));

    marker.placeName = name; // Custom property to track marker's associated place
    parkMarkers.push(marker);
    bounds.push([lat, lon]);
  });

  // Adjust map to fit all markers
  if (bounds.length > 0) {
    map.fitBounds(bounds, { padding: [35, 35] });
  }
}

// When clicking a marker, open the corresponding activity card
function openActivityCardByPlace(placeName) {
  const matchingCard = activityCards.get(placeName);
  if (matchingCard) {
    const matchingMarker = parkMarkers.find(marker => marker.placeName === placeName);
    if (matchingMarker) {
      matchingMarker.openPopup();
    }
  }
}

// Initialize Leaflet map
function initMap() {
  map = L.map('map');

  // Set tile layer from CartoDB
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap & contributors, &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map);

  renderMapMarkers(parkData); // Initial load of park markers
  setTimeout(() => map.invalidateSize(), 200); // Fix for layout resizing issues
  addUserLocationMarker(); // Optionally add user's marker
}

// Add "You are here" marker if geolocation available
function addUserLocationMarker() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        L.marker([latitude, longitude], {
          icon: L.icon({
            iconUrl: "https://maps.gstatic.com/mapfiles/api-3/images/spotlight-poi2_hdpi.png",
            iconSize: [27, 43],
            iconAnchor: [13, 41],
            popupAnchor: [0, -36]
          })
        }).addTo(map)
          .bindPopup('<strong>You are here</strong>');
      },
      (error) => {
        console.error('Error getting user location:', error);
      }
    );
  } else {
    console.error('Geolocation not supported by this browser.');
  }
}

// Load more activities via AJAX
async function loadMoreActivities() {
  const button = document.getElementById('load-more-btn');
  button.disabled = true;
  button.innerText = 'Loading...';

  try {
    // Determine which page to load next
    let currentPage = parseInt(sessionStorage.getItem('currentPage')) || 6;
    sessionStorage.setItem('currentPage', currentPage + 5);

    const res = await fetch('/load_more', {
      method: 'POST',
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ page: currentPage })
    });

    button.disabled = false;
    button.innerText = 'Load More Activities';

    if (!res.ok) {
      console.error('Failed to load more activities');
      return;
    }

    const data = await res.json();
    const container = document.getElementById('results-container');

    // Create and append new activity cards
    data.activities.forEach(activity => {
      const card = document.createElement('div');
      card.className = 'activity-card';
      card.setAttribute('data-place-name', activity.location);

      card.innerHTML = `
        <div class="card-header">
          <h2>${activity.name}</h2>
          <p class="location">${activity.location}</p>
        </div>
        <p class="category"><strong>Category:</strong> ${activity.category}</p>
        <p class="age"><strong>Age:</strong> ${activity.age_description}</p>
        <div class="schedule">
          <table>
            <thead><tr><th>Date</th><th>Time</th><th>Register</th><th>More Info</th></tr></thead>
            <tbody>
              ${activity.date_ranges.map((date, i) => `
                <tr>
                  <td>${date}</td>
                  <td>${activity.time_ranges[i]}</td>
                  <td>${activity.action_links[i] ? `<a href="${activity.action_links[i]}" target="_blank">Register</a>` : '-'}</td>
                  <td>${activity.detail_links[i] ? `<a href="${activity.detail_links[i]}" target="_blank">More Info</a>` : '-'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
        <p class="desc">${activity.desc || ''}</p>
      `;

      container.appendChild(card);
      activityCards.set(activity.location, card);
    });

    renderMapMarkers(data.activity_parks); // Add new parks to the map

    if (!data.more_results_to_fetch) {
      button.style.display = 'none'; // Hide button if no more pages
    }
  } catch (error) {
    console.error('Error while loading more activities:', error);
  }
}

// Reset paging between sessions
function resetPage() {
  sessionStorage.setItem('currentPage', 6);
}

// Initialize event listeners when page loads
document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('results-container');

  // Clicking on a card opens corresponding marker popup
  container.addEventListener('click', (event) => {
    const card = event.target.closest('.activity-card');
    if (!card) return;
    const placeName = card.getAttribute('data-place-name');
    const matchingMarker = parkMarkers.find(marker => marker.placeName === placeName);
    if (matchingMarker) {
      matchingMarker.openPopup();
    }
  });

  initMap(); // Start everything
});
