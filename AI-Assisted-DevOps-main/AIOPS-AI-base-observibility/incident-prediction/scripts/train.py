import os
import datetime
import joblib
import pandas as pd
from prometheus_api_client import PrometheusConnect
from prophet import Prophet

# 1. Connect to Prometheus
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

def fetch_historical_metrics(metric_query, days_back=7):
    print(f"Fetching historical data over the last {days_back} days...")
    
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=days_back)
    
    # Fetch range data using custom PromQL expression
    metric_data = prom.custom_query_range(
        query=metric_query,
        start_time=start_time,
        end_time=end_time,
        step="5m"
    )
    
    if not metric_data:
        raise ValueError("No historical metrics found. Check your Prometheus PromQL expression.")
        
    timestamps = []
    values = []
    
    series = metric_data[0]['values']
    for timestamp, val in series:
        timestamps.append(datetime.datetime.fromtimestamp(timestamp))
        values.append(float(val))
        
    df = pd.DataFrame({'ds': timestamps, 'y': values})
    return df

def train_forecasting_model(df, model_path="memory_prophet_model.joblib"):
    print("Initializing Prophet model for memory tracking...")

    model = Prophet(
        changepoint_prior_scale=0.1, 
        yearly_seasonality=False, 
        weekly_seasonality=True, 
        daily_seasonality=True
    )
    
    print("Training model on historical memory trends...")
    model.fit(df)
    
    joblib.dump(model, model_path)
    print(f"Model successfully saved to {model_path}!")

if __name__ == "__main__":
    # PromQL for Node Memory Utilization Percentage
    MEMORY_METRIC_QUERY = "100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))"
    
    try:
        raw_df = fetch_historical_metrics(MEMORY_METRIC_QUERY, days_back=7)
        train_forecasting_model(raw_df)
    except Exception as e:
        print(f"Training Pipeline Failed: {str(e)}")
        

