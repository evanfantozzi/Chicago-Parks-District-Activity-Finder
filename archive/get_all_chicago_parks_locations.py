import httpx
import time
import sqlite3
from lxml import html
from urllib.parse import urljoin
import random

# Initialize SQLite DB connection (if using SQLite, this will create a DB file)
conn = sqlite3.connect('parks.db')
cursor = conn.cursor()

# Create the parks table with latitude and longitude columns if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS parks_scraped (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL
)
''')
conn.commit()

# Function to get latitude and longitude from an address using Nominatim
def get_lat_long(address):
    # URL encode the address to make it safe for URL query
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "addressdetails": 1,
        "limit": 1
    }

# Starting URL
base_url = "https://www.chicagoparkdistrict.com/parks-facilities?page=246"
current_page_url = base_url

# Initialize httpx client
client = httpx.Client()

while current_page_url:
    print(f"Scraping page: {current_page_url}")
    
    # Fetch the page content using httpx
    response = client.get(current_page_url)
    tree = html.fromstring(response.content)

    # Grab all park sidebar blocks on the current page
    park_blocks = tree.xpath('//div[contains(@class, "node--view-mode-map-sidebar") and contains(@class, "park-sidebar")]')

    print(f"Found {len(park_blocks)} parks.")

    # Loop through each park block to get the title, address, and coordinates
    for i, block in enumerate(park_blocks):
        # Extract the park title
        title_elem = block.xpath('.//h3[@class="thumbnail-object-title"]/a/text()')
        title = title_elem[0].strip() if title_elem else 'No title found'

        address = block.xpath('.//div[contains(@class, "field--name-field-location-address")]//p[@class="address"]/text()')
        address = address[0].strip() if address else ''

        
        print(f"Park {i+1}: {title}")
        print(f"Address: {address}")
        print("------")
        
        # Insert park data into the database with latitude and longitude
        cursor.execute('''
        INSERT INTO parks_scraped (title, address, latitude, longitude) VALUES (?, ?, ?, ?)
        ''', (title, address, None, None))
        conn.commit()
  

    # Check for the next page by looking for the 'next' page link
    next_page_rel = tree.xpath('//a[contains(@title, "Go to next page")]/@href')
    if next_page_rel:
        next_page_url = urljoin(base_url, next_page_rel[0])  # Build absolute URL for the next page
        print(f"Next page found: {next_page_url}")

        # Sleep for 1 second before making the next request
        time.sleep(random.uniform(10, 15))

        current_page_url = next_page_url
    else:
        print("No more pages to scrape.")
        break

# Close the httpx client and DB connection after scraping is done
client.close()
conn.close()