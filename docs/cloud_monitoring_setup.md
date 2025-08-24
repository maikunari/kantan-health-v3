# Google Cloud Monitoring Integration

## Overview
This integration provides real-time API cost tracking using Google Cloud Monitoring metrics, comparing actual API usage with local estimates.

## Setup Instructions

### 1. Enable Cloud Monitoring API
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to APIs & Services → Enable APIs
3. Search for "Cloud Monitoring API"
4. Click Enable

### 2. Set Up Authentication

#### Option A: Using gcloud CLI (Recommended)
```bash
# Install gcloud CLI
brew install --cask google-cloud-sdk  # macOS
# Or download from: https://cloud.google.com/sdk/install

# Authenticate
gcloud auth application-default login
```

#### Option B: Using Service Account
```bash
# Create service account and download key
gcloud iam service-accounts create healthcare-monitoring \
  --display-name="Healthcare Directory Monitoring"

gcloud iam service-accounts keys create ~/monitoring-key.json \
  --iam-account=healthcare-monitoring@YOUR_PROJECT.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/monitoring-key.json
```

### 3. Grant Permissions
The service account needs the following permissions:
- `monitoring.timeSeries.list` - to read metrics
- `serviceusage.services.use` - to access API usage data

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT \
  --member="serviceAccount:healthcare-monitoring@YOUR_PROJECT.iam.gserviceaccount.com" \
  --role="roles/monitoring.viewer"
```

### 4. Install Dependencies
```bash
pip3 install google-cloud-monitoring
```

## Usage

### Test Cloud Monitoring Connection
```bash
python3 scripts/test_cloud_monitoring.py
```

Expected output:
```
=== Google Cloud Monitoring - Actual Usage ===
Text Search API calls today: 45
Nearby Search API calls today: 0  
Place Details API calls today: 134
Total API calls: 179

Estimated cost (local tracking): $9.97
Actual cost (Cloud Monitoring): $5.72
Difference: $4.25
```

### Real-time Monitoring Dashboard
```bash
# With Cloud Monitoring
python3 scripts/monitor_api_costs.py

# Without Cloud Monitoring (estimates only)
python3 scripts/monitor_api_costs.py --no-cloud

# Custom refresh rate (default: 60 seconds)
python3 scripts/monitor_api_costs.py --refresh 30
```

## API Metrics Tracked

The system monitors these Google Maps Platform metrics:
- `maps.googleapis.com/quotas/text_search_requests/usage`
- `maps.googleapis.com/quotas/nearby_search_requests/usage`
- `maps.googleapis.com/quotas/place_details_requests/usage`

## Cost Calculations

### Retail Pricing (as of 2024)
- Text Search: $0.032 per request
- Nearby Search: $0.032 per request
- Place Details: $0.017 per request

### Free Tier
Google provides $200/month free credit which significantly reduces actual costs.

## Integration Features

### CostTracker Enhancement
The `CostTracker` class now:
1. Attempts to connect to Cloud Monitoring on initialization
2. Falls back to estimate-based tracking if unavailable
3. Uses the higher value (actual vs estimated) for conservative budgeting
4. Logs both values for comparison

### New Methods
- `get_actual_vs_estimated()` - Returns comparison data
- `CloudMonitoringCostTracker.get_actual_api_calls_today()` - Gets real API call counts
- `CloudMonitoringCostTracker.get_actual_cost_today()` - Calculates actual costs
- `CloudMonitoringCostTracker.get_remaining_budget()` - Shows remaining daily budget

## Troubleshooting

### "Credentials not found" Error
```bash
# Check if credentials are configured
gcloud auth application-default print-access-token

# Re-authenticate if needed
gcloud auth application-default login
```

### "API not enabled" Error
Enable the Cloud Monitoring API in Google Cloud Console.

### "Permission denied" Error
Ensure your service account has the `monitoring.viewer` role.

### Metrics Not Appearing
- Cloud Monitoring metrics may have a few minutes delay
- Ensure you've made actual API calls to Google Maps Platform
- Check the correct project is being used

## Benefits

1. **Accurate Cost Tracking**: See actual API usage instead of estimates
2. **Free Tier Visibility**: Understand savings from Google's free credits
3. **Real-time Monitoring**: Track costs as they occur
4. **Budget Protection**: Conservative approach using max(actual, estimated)
5. **Debugging**: Compare estimates with reality to calibrate tracking

## Notes

- Cloud Monitoring data may have 1-5 minute delay
- Free tier and discounts are not reflected in calculated costs
- The system uses the higher of actual vs estimated for safety
- Cache hits are tracked separately in local database