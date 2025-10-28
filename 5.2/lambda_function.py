import json
import boto3
import pandas as pd
import joblib
import os
import numpy as np
from sklearn.exceptions import NotFittedError

bucket_name = os.environ['BUCKET_NAME']
remote_model_key = os.environ['REMOTE_KEY']
local_model_key = f"/tmp/{remote_model_key}"

def lambda_handler(event, context):
    # CORS handling
    origin = event['headers'].get('origin', '')

    # Validating and extracting query parameters
    query_params = event.get("queryStringParameters", {})
    required_params = ['brand', 'model', 'model_year', 'mileage', 'horsepower', 'color']

    if not all(param in query_params for param in required_params):
        return {"statusCode": 400, "body": "Missing required query parameters"}

    try:
        brand = int(query_params["brand"])
        model = int(query_params["model"])
        model_year = int(query_params["model_year"])
        mileage = int(float(query_params["mileage"]))
        horsepower = int(float(query_params["horsepower"]))
        color = int(query_params["color"])
    except ValueError:
        return {"statusCode": 400, "body": "Invalid parameter types"}

    # Load model
    if not os.path.exists(local_model_key):
        boto3.client("s3").download_file(bucket_name, remote_model_key, local_model_key)

    # Predict
    try:
        trained_model = joblib.load(local_model_key)
        input_data = pd.DataFrame([[brand, model, model_year, mileage, horsepower, color]], columns=["brand", "model", "model_year", "mileage", "horsepower", "color"])
        fiyat_prediction = trained_model.predict(input_data)
        price = int(np.round(fiyat_prediction[0]))
    except NotFittedError:
        return {"statusCode": 500, "body": "Model not fitted"}
    except Exception as e:
        return {"statusCode": 500, "body": f"Prediction error: {str(e)}"}

    # Response
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": origin
        },
        "body": json.dumps({"price": price})
    }
