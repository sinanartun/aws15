import json
import joblib
import pandas as pd
import numpy as np

# Load pipeline at cold start
pipe = joblib.load('model.pkl')

def lambda_handler(event, context):
    try:
        # Parse input
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event
        
        # Create DataFrame from input
        df = pd.DataFrame([body])
        
        # Make prediction (returns log price)
        pred_log = pipe.predict(df)[0]
        
        # Convert back from log
        pred_price = np.expm1(pred_log)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'predicted_price': float(pred_price)})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
