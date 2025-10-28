import json
import os
import csv
import glob

def extract_car_links():
    """Extract all car links from the JSON files in step1 folder"""
    all_links = []

    # Get all JSON files in step1 folder
    json_files = glob.glob('./step1/*.json')

    # Sort files by page number
    json_files.sort(key=lambda x: int(x.split('_')[-2].split('.')[0]))

    for json_file in json_files:
        try:
            print(f"Processing {json_file}...")
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract links from cars array
            if 'cars' in data and isinstance(data['cars'], list):
                for car in data['cars']:
                    if 'link' in car and car['link']:
                        all_links.append(car['link'])

        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")

    return all_links

def create_csv_files(links, chunk_size=100):
    """Create CSV files with chunks of links"""
    # Create step2 folder if it doesn't exist
    if not os.path.exists('./step2'):
        os.makedirs('./step2')

    # Split links into chunks of 100
    for i in range(0, len(links), chunk_size):
        chunk = links[i:i + chunk_size]
        csv_filename = f"./step2/car_links_{i//chunk_size + 1}.csv"

        # Write chunk to CSV
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow(['link'])
            # Write links
            for link in chunk:
                writer.writerow([link])

        print(f"Created {csv_filename} with {len(chunk)} links")

def main():
    print("Starting link extraction...")

    # Extract all car links
    all_links = extract_car_links()

    print(f"Total links extracted: {len(all_links)}")

    # Create CSV files with 100 links each
    create_csv_files(all_links, chunk_size=100)

    print("Link extraction and CSV creation completed!")

if __name__ == "__main__":
    main()
