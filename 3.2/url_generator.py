from datetime import datetime, timedelta
import csv

base_url = "https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1d/BTCUSDT-1d-{}.zip"
end_date = datetime.now()

with open('binance_urls.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['date', 'url'])
    
    for i in range(100):
        date = end_date - timedelta(days=i)
        url = base_url.format(date.strftime("%Y-%m-%d"))
        writer.writerow([date.strftime(url)])
        print(url)