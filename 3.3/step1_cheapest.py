import requests
import os
import json
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

# Create step1 folder if it doesn't exist
if not os.path.exists('step1'):
    os.makedirs('step1')

# Headers from the request
headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,tr;q=0.8,sv;q=0.7",
    "baggage": "sentry-environment=aws-prod,sentry-release=ZsFEwkkpvDviL5f88Ptgm,sentry-public_key=8d1174c069030cfc7b94726f35c342de,sentry-trace_id=5e139e551a30464696b4985417247d4a,sentry-sample_rate=0.1,sentry-transaction=%2F%5Bpage%5D%2F%5Bsubpage%5D,sentry-sampled=false",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sentry-trace": "e81926b67d33472b98ba3058374ada50-b7dc9db45e9ff2cc-0",
    "x-nextjs-data": "1",
    "cookie": "_sp_su=false; _cmp_marketing=1; _cmp_analytics=1; _cmp_advertising=1; _cmp_personalisation=1; consentUUID=dc018a6a-f930-40d4-b455-67c728fa08d5_49; consentDate=2025-10-16T14:38:39.227Z; _gcl_au=1.1.423518817.1760625522; _hjSessionUser_479523=eyJpZCI6IjM1OGUwYjczLTc2ZDgtNWFhMi1hYjg0LTI0MTgwNDhhMTg5MCIsImNyZWF0ZWQiOjE3NjA2MjU1MjE4NTgsImV4aXN0aW5nIjp0cnVlfQ==; _fbp=fb.1.1760629186595.508148531499424891; __codnt=_; _sg_b_v=2%3B3160%3B1761035408; _pulse2data=3cd3e8c5-0708-4290-bd86-d62cbce1c417%2Cv%2C%2C1762275994000%2CeyJpc3N1ZWRBdCI6IjIwMjUtMTAtMTZUMTQ6Mzg6MzdaIiwiZW5jIjoiQTEyOENCQy1IUzI1NiIsInJlSXNzdWVkQXQiOiIyMDI1LTEwLTI4VDE3OjA2OjM0WiIsImFsZyI6ImRpciIsImtpZCI6IjMifQ..FVn4siu2WaIVZwtqq--HnA.mO1fkRobETozEnjJn0EMhuia8eZFvOR0VkBxz50mED_mpnNKF7Fgydneupz-Kha57RaxPRbB_6IOgUqEm1EqKiax9hTjjwICIzT30nCsiqSs7PBthwan-feD1l3IOw7GEp5kW-ZjF9s52owvjuo2hIJBHMvVjwDzgbafiTkPbFYGKghos0kI2ptg5EG1RUDGqYF-7-MGtPzw3GCoGZHVAvlJNWM6ZuGm-lO94DIkFFzngJ0XaRfZmKkCz34mprJDGzrE70B98IaL2XcI96s5cZaX0LeVK1f2AOW-nB3pIukJEEdjYRDCo7z-CQ4VPsh-fLzUizcePE2pyKjWeXNVN7dbbZ2lPvlq_OU1y139lF8o3sfSVCUGBDK5rhAWfUjufw8EwpjN-N_rZIp3Up6AsKlDfSIPRau9j-JOmu7eYNY1lgs6Cekc9d4iKwpmSL0fBwYGBUor61JgyhT5W41nNA.hWecBhv8Weu_6IM8Ql0nzg%2C%2C0%2Ctrue%2C%2CeyJraWQiOiIzIiwiYWxnIjoiSFMyNTYifQ..zFqGNxeMhPEj6H5kmhtXG6FvGfWVTd5nvD3VeNuLPfg; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%222Fcfk9NmuOtokAufuiRe%22%2C%22expiryDate%22%3A%222026-10-28T17%3A06%3A34.566Z%22%7D; _hjSession_479523=eyJpZCI6ImE5ZWQ1YzkyLTVhZmUtNGE3YS05YzE5LWEzMThhODAxNjQyYiIsImMiOjE3NjE2NzExOTUyMTQsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowfQ==; __gads=ID=b1735e07645f69ab:T=1760625519:RT=1761671195:S=ALNI_MaDTaKaHUQ9l50hIS80fRKnhdJFow; __eoi=ID=83a7a79fdc319223:T=1760625519:RT=1761671196:S=AA-AfjbK21aOPdosI1l-2lFwlWln; _pulsesession=%5B%22sdrn%3Aschibsted%3Asession%3Afc1a26c1-0c5a-43f3-9f2c-d60d546aaab1%22%2C1761671194555%2C1761671211688%5D; _dd_s=rum=0&expire=1761672162962",
    "Referer": "https://www.blocket.se/bilar/sok"
}

# Base URL
base_url = "https://www.blocket.se/bilar/_next/data/ZsFEwkkpvDviL5f88Ptgm/sok.json?page="

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
            filename = f"step1/page_{page}_cheapest.json"
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
