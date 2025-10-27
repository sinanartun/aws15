#!/bin/bash

# Test locally (after: docker run -p 9000:8080 car-price-lambda)
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -H "Content-Type: application/json" \
  -d '{
    "body": "{\"mileage_log\": 10.5, \"horsepower\": 150, \"equipment_count\": 45, \"vehicle_age\": 5, \"days_since_first_traffic\": 1825, \"subject_len\": 50, \"brand\": \"Volvo\", \"model\": \"V60\", \"model_family\": \"V60\", \"fuel\": \"Diesel\", \"gearbox\": \"Automat\", \"color\": \"Svart\", \"drive_wheels\": \"Fyrhjulsdriven\", \"body_type\": \"Kombi\", \"advertiser_type\": \"store\", \"region\": \"Stockholm\", \"municipality\": \"Stockholm\", \"region_municipality\": \"Stockholm | Stockholm\"}"
  }'
