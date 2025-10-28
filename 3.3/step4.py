import json
import os
import csv
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

def extract_car_features(json_file):
    """Extract relevant features from a single JSON file"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        car_data = data.get('data', {})
        
        # Extract basic info
        features = {
            'ad_id': car_data.get('ad_id', ''),
            'price': car_data.get('price', {}).get('value', ''),
            'subject': car_data.get('subject', ''),
        }
        
        # Extract from parameter_groups
        for group in car_data.get('parameter_groups', []):
            for param in group.get('parameters', []):
                param_id = param.get('id')
                param_value = param.get('value', '')
                
                if param_id == 'fuel':
                    features['fuel'] = param_value
                elif param_id == 'gearbox':
                    features['gearbox'] = param_value
                elif param_id == 'mileage':
                    features['mileage'] = param_value.replace(' ', '')
                elif param_id == 'regdate':
                    features['model_year'] = param_value
                elif param_id == 'cx_make':
                    features['brand'] = param_value
                elif param_id == 'cx_engine_power':
                    features['horsepower'] = param_value
                elif param_id == 'cx_model':
                    features['model'] = param_value
                elif param_id == 'cx_color':
                    features['color'] = param_value
                elif param_id == 'cx_first_time_in_traffic':
                    features['first_traffic_date'] = param_value
                elif param_id == 'cx_drive_wheels':
                    features['drive_wheels'] = param_value
                elif param_id == 'car_chassis_type':
                    features['body_type'] = param_value
                elif param_id == 'level_1':
                    features['model_family'] = param_value
        
        # Extract equipment count
        equipment_count = 0
        for attr in car_data.get('attributes', []):
            if attr.get('id') == 'car_equipment':
                equipment_count = len(attr.get('items', []))
        features['equipment_count'] = equipment_count
        
        # Extract advertiser type
        features['advertiser_type'] = car_data.get('advertiser', {}).get('type', '')
        
        # Extract location
        location = car_data.get('location', [])
        features['region'] = location[0].get('name', '') if len(location) > 0 else ''
        features['municipality'] = location[1].get('name', '') if len(location) > 1 else ''
        
        return features
        
    except Exception as e:
        print(f"Error processing {json_file}: {str(e)}")
        return None

def process_json_files(step3_folder, output_csv, max_workers):
    """Process all JSON files and create CSV"""
    
    json_files = [os.path.join(step3_folder, f) for f in os.listdir(step3_folder) if f.endswith('.json')]
    
    print(f"Found {len(json_files)} JSON files to process")
    
    all_features = []
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(extract_car_features, f): f for f in json_files}
        
        processed = 0
        for future in as_completed(future_to_file):
            features = future.result()
            if features:
                all_features.append(features)
            
            processed += 1
            if processed % 100 == 0:
                print(f"Progress: {processed}/{len(json_files)} files processed")
    
    # Write to CSV
    if all_features:
        fieldnames = ['ad_id', 'price', 'subject', 'brand', 'model', 'model_family', 'model_year', 
                      'mileage', 'fuel', 'gearbox', 'horsepower', 'color', 'drive_wheels', 
                      'body_type', 'first_traffic_date', 'equipment_count', 'advertiser_type', 
                      'region', 'municipality']
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_features)
        
        print(f"\nSuccessfully created {output_csv} with {len(all_features)} records")
    else:
        print("No data extracted")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    step3_folder = os.path.join(script_dir, 'step3')
    output_csv = os.path.join(script_dir, 'car_features_short.csv')
    
    if not os.path.exists(step3_folder):
        print(f"Error: {step3_folder} folder not found")
        return
    
    max_workers = min(8, multiprocessing.cpu_count())
    print(f"Using {max_workers} processes")
    
    process_json_files(step3_folder, output_csv, max_workers)
    print("\nProcessing complete!")

if __name__ == "__main__":
    main()
