import os
import time
import datetime
import requests
import joblib
import pandas as pd
from prometheus_api_client import PrometheusConnect

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/YOUR/WEBHOOK/LINK")
MODEL_PATH = "memory_prophet_model.joblib"
CRITICAL_THRESHOLD = 95.0  # Alert when memory is predicted to hit 95%+

prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

def send_slack_alert(current_val, time_to_exhaustion_mins, breach_time_str):
    
    payload = {
        "text": "🚨 *AIOps Proactive Memory Exhaustion Alert* 🚨",
        "attachments": [
            {
                "color": "#FF8C00", # Warning Amber/Red
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"⚠️ *Predictive Incident Warning:* System calculated high risk of memory saturation.\n"
                                    f"👉 *Estimated to exhaust available memory in  {time_to_exhaustion_mins} minutes.*"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Current Memory Usage:* \n{current_val:.2f}%"},
                            {"type": "mrkdwn", "text": f"*Target Limit:* \n{CRITICAL_THRESHOLD}%"},
                            {"type": "mrkdwn", "text": f"*Predicted Breach Time:* \n{breach_time_str}"}
                        ]
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            print("Successfully routed predictive alert payload to Slack.")
    except Exception as e:
        print(f"Failed to transmit message to Slack webhook: {str(e)}")

def run_inference_cycle():
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model file '{MODEL_PATH}' not found.")
        return

    model = joblib.load(MODEL_PATH)
    MEMORY_METRIC_QUERY = "100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))"

    metric_data = prom.custom_query(query=MEMORY_METRIC_QUERY)
    
    if not metric_data:
        print("Could not retrieve real-time state for inference cycle.")
        return
        
    current_value = float(metric_data[0]['value'][1])
    
   
    future_dataframe = model.make_future_dataframe(periods=24, freq='5min', include_history=False)
    forecast = model.predict(future_dataframe)
  
    breach_rows = forecast[forecast['yhat'] >= CRITICAL_THRESHOLD]
    
    if not breach_rows.empty:
        earliest_breach = breach_rows.iloc[0]
        breach_timestamp = earliest_breach['ds']
        

        now_utc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        time_to_exhaustion_mins = (breach_timestamp - now_utc).total_seconds() / 60.0
        
        # Only alert if the exhaustion event falls within our 2-hour runway
        if time_to_exhaustion_mins > 0:
            breach_time_str = breach_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
            print(f"Warning: Memory saturation predicted in {time_to_exhaustion_mins:.1f} minutes.")
            send_slack_alert(current_value, time_to_exhaustion_mins, breach_time_str)
    else:
        print("System metric trajectory clear. No memory saturation events predicted within 2 hours.")

if __name__ == "__main__":
    print("Memory Inference daemon initialized...")
    while True:
        run_inference_cycle()
        time.sleep(300) # Re-evaluate every 5 minutes