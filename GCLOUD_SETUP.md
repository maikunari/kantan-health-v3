# Google Cloud Authentication Setup Guide

## Complete Authentication Process

### Step 1: Run the Authentication Command
Open Terminal and run:
```bash
gcloud auth application-default login
```

### Step 2: Complete Browser Authentication
1. Your browser will open automatically (or you'll get a URL to copy/paste)
2. Sign in with your Google account
3. Grant the requested permissions:
   - View your email address
   - See, edit, configure, and delete Google Cloud data
   - Administer Cloud SQL

### Step 3: Verify Authentication
After completing the browser steps, your terminal should show:
```
Credentials saved to file: [/Users/michaelsewell/.config/gcloud/application_default_credentials.json]
```

### Step 4: Test the Authentication
Run this command to verify:
```bash
gcloud auth application-default print-access-token
```

If successful, you'll see an access token printed.

## Alternative: Set Your Project ID

If you know your Google Cloud Project ID, set it:
```bash
gcloud config set project YOUR_PROJECT_ID
```

To list your projects:
```bash
gcloud projects list
```

## Test Cloud Monitoring Integration

Once authenticated, test the integration:
```bash
python3 scripts/test_cloud_monitoring.py
```

## Troubleshooting

### If you get "API not enabled" error:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to APIs & Services → Enable APIs
3. Search for "Cloud Monitoring API"
4. Click Enable

### If you get "Permission denied" error:
Your account needs the Monitoring Viewer role. Have your admin run:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT \
  --member="user:YOUR_EMAIL@gmail.com" \
  --role="roles/monitoring.viewer"
```

### To check your current authentication:
```bash
# Show current authenticated account
gcloud auth list

# Show application default credentials
gcloud auth application-default print-access-token

# Show current project
gcloud config get-value project
```

## Required APIs
Make sure these APIs are enabled in your Google Cloud project:
1. **Cloud Monitoring API** - for reading metrics
2. **Maps Platform APIs** - for Places API usage

## Environment Variables (Optional)
If you prefer using a service account key file instead:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## Next Steps
After authentication is complete:
1. Test Cloud Monitoring: `python3 scripts/test_cloud_monitoring.py`
2. Monitor costs in real-time: `python3 scripts/monitor_api_costs.py`
3. The system will now show actual API usage vs estimates

## Notes
- Application Default Credentials are stored in: `~/.config/gcloud/application_default_credentials.json`
- These credentials expire after 1 hour but are automatically refreshed
- The credentials are used by all Google Cloud client libraries automatically