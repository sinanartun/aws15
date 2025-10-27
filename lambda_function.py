import json
import mysql.connector

def lambda_handler(event, context):
    """
    Lambda function that fetches all data from RDS MySQL database.
    """
    
    connection = None
    try:
        connection = mysql.connector.connect(
            host='database-1.c1ueeskysdez.eu-north-1.rds.amazonaws.com',
            user='admin',
            password='haydegidelum',
            port=63306,
            database='cars'
        )
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cars")
        results = cursor.fetchall()
        cursor.close()
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(results, default=str)
        }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
    
    finally:
        if connection:
            connection.close()
