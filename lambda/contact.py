import json
import boto3
from botocore.exceptions import ClientError

RECIPIENT = "rico@whereisrico.dev"
SENDER = "rico@whereisrico.dev"

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


def lambda_handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": CORS_HEADERS, "body": ""}

    try:
        body = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Invalid JSON body"}),
        }

    name = body.get("name", "").strip()
    email = body.get("email", "").strip()
    message = body.get("message", "").strip()

    missing = [f for f, v in [("name", name), ("email", email), ("message", message)] if not v]
    if missing:
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": f"Missing required fields: {', '.join(missing)}"}),
        }

    subject = f"Contact form message from {name}"
    body_text = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
    body_html = f"""
    <p><strong>Name:</strong> {name}</p>
    <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
    <p><strong>Message:</strong></p>
    <p>{message.replace(chr(10), '<br>')}</p>
    """

    ses = boto3.client("ses")
    try:
        ses.send_email(
            Source=SENDER,
            Destination={"ToAddresses": [RECIPIENT]},
            Message={
                "Subject": {"Data": subject},
                "Body": {
                    "Text": {"Data": body_text},
                    "Html": {"Data": body_html},
                },
            },
            ReplyToAddresses=[email],
        )
    except ClientError as e:
        print(f"SES error: {e.response['Error']['Message']}")
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Failed to send message. Please try again later."}),
        }

    return {
        "statusCode": 200,
        "headers": CORS_HEADERS,
        "body": json.dumps({"message": "Message sent successfully"}),
    }
