import requests
import os
import csv
import time
import sys

def process_single_csv(csv_filename):
    """Process a single CSV file from step2 folder and fetch detailed data for each car"""

    # Create step3 folder if it doesn't exist
    if not os.path.exists('step3'):
        os.makedirs('step3')

    # Headers from the request
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9,tr;q=0.8,sv;q=0.7",
        "authorization": "Bearer edfea0488e0e0f490cd95e134bb8907fb92a6273",
        "priority": "u=1, i",
        "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site"
    }

    # Base URL for the detailed API
    base_url = "https://api.blocket.se/search_bff/v2/content/{}?include=store&include=partner_placements&include=breadcrumbs&include=archived&include=car_condition&include=home_delivery&include=realestate&status=active&status=deleted&status=hidden_by_user"

    processed_count = 0
    error_count = 0

    try:
        print(f"Processing CSV file: {csv_filename}")

        # Read the CSV file
        with open(csv_filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                link = row['link'].strip()

                # Extract ID from the link (format: https://www.blocket.se/annons/{id})
                try:
                    car_id = link.split('/annons/')[-1]
                    if not car_id:
                        print(f"Could not extract ID from link: {link}")
                        error_count += 1
                        continue

                    # Construct API URL
                    api_url = base_url.format(car_id)

                    # Make the request
                    response = requests.get(api_url, headers=headers)

                    if response.status_code == 200:
                        # Save the JSON data to step3 folder
                        filename = f"step3/{car_id}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            response.json()  # This will raise an exception if not valid JSON
                            f.write(response.text)  # Save raw response

                        processed_count += 1
                        print(f"Successfully processed car ID: {car_id}")

                    else:
                        print(f"Failed to fetch data for car ID {car_id} - Status code: {response.status_code}")
                        error_count += 1

                except Exception as e:
                    print(f"Error processing link {link}: {str(e)}")
                    error_count += 1

                # Add a small delay to be respectful to the API
                time.sleep(0.2)

    except FileNotFoundError:
        print(f"CSV file not found: {csv_filename}")
        return False
    except Exception as e:
        print(f"Error processing CSV file: {str(e)}")
        return False

    print(f"Completed processing {csv_filename}")
    print(f"Successfully processed: {processed_count} cars")
    print(f"Errors: {error_count} cars")
    return True

def main():
    # Check if CSV filename is provided as command line argument
    if len(sys.argv) != 2:
        print("Usage: python step3.py <csv_filename>")
        print("Example: python step3.py step2/car_links_1.csv")
        print("\nAvailable CSV files in step2 folder:")
        if os.path.exists('step2'):
            csv_files = [f for f in os.listdir('step2') if f.endswith('.csv')]
            for csv_file in sorted(csv_files):
                print(f"  {csv_file}")
        return

    csv_filename = sys.argv[1]

    # Process the specified CSV file
    success = process_single_csv(csv_filename)

    if success:
        print("Processing completed successfully!")
    else:
        print("Processing failed!")

if __name__ == "__main__":
    main()
