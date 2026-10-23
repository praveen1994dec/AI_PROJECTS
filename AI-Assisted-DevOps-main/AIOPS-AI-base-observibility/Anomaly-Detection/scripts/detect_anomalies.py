import joblib
import requests
import numpy as np
import time
import os
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
MODEL_FILE = "aiops_model.joblib"
PROM_URL = config['monitoring']['prometheus_url']
QUERY = config['monitoring']['query']
SLACK_WEBHOOK = config['monitoring']['slack_webhook']

def get_cpu():
    try:
        response = requests.get(
            f"{PROM_URL}/api/v1/query",
            params={"query": QUERY},
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        return float(data["data"]["result"][0]["value"][1])
    except Exception as e:
        print(f"⚠️ Fetch error: {str(e)}")
        return None

def alert_slack(message):
    try:
        requests.post(
            SLACK_WEBHOOK,
            json={"text": message},
            timeout=5
        )
        print("✅ Slack alert sent")
    except Exception as e:
        print(f"⚠️ Slack alert failed: {str(e)}")

if __name__ == "__main__":
    if not os.path.exists(MODEL_FILE):
        exit("❌ Model file not found - run train_model.py first")
    if not os.path.exists('config.ini'):
        exit("❌ config.ini not found")
    if SLACK_WEBHOOK == "YOUR_SLACK_WEBHOOK_URL":
        print("⚠️ Warning: Please configure Slack webhook in config.ini")
        
    model = joblib.load(MODEL_FILE)
    print("✅ AIOps detector started. Monitoring CPU...")
    
    while True:
        cpu = get_cpu()
        if cpu is not None:
            pred = model.predict([[cpu]])
            if pred[0] == -1:
                msg = f"🚨 CPU Anomaly Detected: {cpu:.2f}%"
                print(msg)
                alert_slack(msg)
            else:
                print(f"✅ CPU Normal: {cpu:.2f}%")
        time.sleep(30)