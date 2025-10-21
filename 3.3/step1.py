import requests
import os
import json
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

# Create step1 folder if it doesn't exist
if not os.path.exists('./step1'):
    os.makedirs('./step1')

# Headers from the request
headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,tr;q=0.8,sv;q=0.7",
    "authorization": "Bearer 68b344934a3e82790b9982eb654790b69a14bde5",
    "cache-control": "max-age=0",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site"
}

# Base URL
base_url = "https://api.blocket.se/motor-search-service/v4/search/car?page="

def download_page(page):
    """Download a single page and return the result"""
    try:
        # Construct the URL for current page
        url = f"{base_url}{page}"

        # Make the request
        response = requests.get(url, headers=headers)

        # Check if request was successful
        if response.status_code == 200:
            # Save the JSON data to a file
            filename = f"./step1/page_{page}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, indent=2, ensure_ascii=False)

            return f"Successfully downloaded page {page}"
        else:
            return f"Failed to download page {page} - Status code: {response.status_code}"

    except Exception as e:
        return f"Error downloading page {page}: {str(e)}"

def main():
    # Number of concurrent processes (adjust based on your system and API limits)
    max_workers = min(8, multiprocessing.cpu_count())

    print(f"Starting download with {max_workers} processes...")

    # Create a list of all pages to download
    pages = list(range(1, 401))

    # Use ProcessPoolExecutor for multiprocessing
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_page = {executor.submit(download_page, page): page for page in pages}

        # Process results as they complete
        completed = 0
        for future in as_completed(future_to_page):
            page = future_to_page[future]
            try:
                result = future.result()
                print(result)
                completed += 1
                if completed % 50 == 0:  # Progress update every 50 pages
                    print(f"Progress: {completed}/400 pages completed")
            except Exception as exc:
                print(f'Page {page} generated an exception: {exc}')

    print("Download process completed!")

if __name__ == "__main__":
    main()
