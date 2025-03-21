def lambda_handler(event, context):
    print("Test Lambda invoked with event:")
    print(event)
    
    # Return success response with received event
    return {
        "statusCode": 200,
        "body": "Test Lambda executed successfully!",
        "received_event": event
    }
