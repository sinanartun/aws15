import requests
import os
import csv
import sys
import multiprocessing
import random
from concurrent.futures import ProcessPoolExecutor, as_completed

def fetch_car_data(args):
    """Fetch data for a single car ID"""
    car_id, step3_folder, headers, base_url = args
    
    try:
        api_url = base_url.format(car_id)
        response = requests.get(api_url, headers=headers,timeout=5)
        
        if response.status_code == 200:
            filename = os.path.join(step3_folder, f"{car_id}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            return (True, car_id, None)
        else:
            return (False, car_id, f"Status code: {response.status_code}")
    except Exception as e:
        return (False, car_id, str(e))

def process_single_csv(csv_filename, step3_folder, headers, base_url, max_workers):
    """Process a single CSV file from step2 folder and fetch detailed data for each car"""
    
    try:
        print(f"\nProcessing: {os.path.basename(csv_filename)}")
        
        car_ids = []
        with open(csv_filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                link = row['link'].strip()
                car_id = link.split('/annons/')[-1]
                if car_id:
                    car_ids.append(car_id)
        
        print(f"Found {len(car_ids)} cars to process")
        
        args_list = [(car_id, step3_folder, headers, base_url) for car_id in car_ids]
        
        processed_count = 0
        error_count = 0
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_car = {executor.submit(fetch_car_data, args): args[0] for args in args_list}
            
            for future in as_completed(future_to_car):
                success, car_id, error = future.result()
                if success:
                    processed_count += 1
                else:
                    error_count += 1
                    print(f"Failed to fetch car ID {car_id}: {error}")
                
                if (processed_count + error_count) % 50 == 0:
                    print(f"Progress: {processed_count + error_count}/{len(car_ids)} completed")
        
        print(f"Completed processing {csv_filename}")
        print(f"Successfully processed: {processed_count} cars")
        print(f"Errors: {error_count} cars")
        return True
        
    except Exception as e:
        print(f"Error processing CSV file: {str(e)}")
        return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    step2_folder = os.path.join(script_dir, 'step2')
    step3_folder = os.path.join(script_dir, 'step3')
    
    if not os.path.exists(step3_folder):
        os.makedirs(step3_folder)
    
    headers = {
        "accept": "*/*",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "authorization": "Bearer 24f35042d5602f6c55d6969623d643c6477e38c8",
        "priority": "u=1, i",
        "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site"
    }
    
    base_url = "https://api.blocket.se/search_bff/v2/content/{}?include=store&include=partner_placements&include=breadcrumbs&include=archived&include=car_condition&include=home_delivery&include=realestate&status=active&status=deleted&status=hidden_by_user"
    
    max_workers = min(32, multiprocessing.cpu_count())
    print(f"Using {max_workers} processes")
    
    if not os.path.exists(step2_folder):
        print(f"Error: {step2_folder} folder not found")
        return
    
    csv_files = [f for f in os.listdir(step2_folder) if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in step2 folder")
        return
    
    print(f"Found {len(csv_files)} CSV files total")
    print("Starting continuous random scraping (Ctrl+C to stop)\n")
    
    processed_files = set()
    
    try:
        while len(processed_files) < len(csv_files):
            # Select a random unprocessed CSV file
            available_files = [f for f in csv_files if f not in processed_files]
            random_csv = random.choice(available_files)
            
            print(f"\n[{len(processed_files) + 1}/{len(csv_files)}] Randomly selected: {random_csv}")
            
            csv_path = os.path.join(step2_folder, random_csv)
            if process_single_csv(csv_path, step3_folder, headers, base_url, max_workers):
                processed_files.add(random_csv)
        
        print("\n✓ All files processed!")
    
    except KeyboardInterrupt:
        print(f"\n\nStopped by user. Processed {len(processed_files)}/{len(csv_files)} files")

if __name__ == "__main__":
    main()
