from fastapi import FastAPI, Request
import json
import datetime

app = FastAPI()

WEBHOOK_FILE = "webhook_requests.txt"

# Function to save webhook data to a file
def save_webhook_data(data):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(WEBHOOK_FILE, "a") as f:
        f.write(f"Timestamp: {timestamp}\n")
        f.write(json.dumps(data, indent=2))
        f.write("\n" + "-" * 50 + "\n")

# Webhook Endpoint (POST)
@app.post("/")
async def receive_webhook(request: Request):
    data = await request.json()
    save_webhook_data(data)
    return {"message": "Webhook received", "data": data}

# Endpoint to view received webhook data
@app.get("/view")
def view_webhook_data():
    try:
        with open(WEBHOOK_FILE, "r") as f:
            return {"webhooks": f.read()}
    except FileNotFoundError:
        return {"message": "No webhooks received yet"}
