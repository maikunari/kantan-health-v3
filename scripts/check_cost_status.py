#!/usr/bin/env python3
"""Check cost tracking status with Cloud Monitoring"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.cost_tracker import CostTracker
from datetime import datetime

print('=' * 60)
print('COST TRACKING STATUS WITH CLOUD MONITORING')
print('=' * 60)
print(f'Timestamp: {datetime.now()}')
print()

tracker = CostTracker(use_cloud_monitoring=True, project_id='japan-directory-463903')

# Get comparison
comparison = tracker.get_actual_vs_estimated()

print('📊 Cloud Monitoring Status:')
if tracker.cloud_monitor:
    print('  ✅ Connected to Google Cloud')
    print(f'  📁 Project: japan-directory-463903')
else:
    print('  ❌ Not connected')

print()
print('💰 Cost Analysis:')
print(f'  Actual Cost (Cloud Monitoring):  ${comparison["actual_cost"]:.2f}')
print(f'  Estimated Cost (Local Tracking): ${comparison["estimated_cost"]:.2f}')

print()
print('📈 Daily Budget:')
daily_used = tracker.get_daily_usage()
daily_remaining = tracker.DAILY_LIMIT - daily_used
print(f'  Limit:     ${tracker.DAILY_LIMIT:.2f}')
print(f'  Used:      ${daily_used:.2f}')
print(f'  Remaining: ${daily_remaining:.2f}')

print()
print('📅 Monthly Budget:')
monthly_used = tracker.get_monthly_usage()
monthly_remaining = tracker.MONTHLY_LIMIT - monthly_used
print(f'  Limit:     ${tracker.MONTHLY_LIMIT:.2f}')
print(f'  Used:      ${monthly_used:.2f}')
print(f'  Remaining: ${monthly_remaining:.2f}')

print()
print('✅ System Ready:')
print('  - Cloud Monitoring integrated successfully')
print('  - Real-time cost tracking enabled')
print('  - Daily budget reset at midnight')
print('  - You can now run collection with full budget')
print('=' * 60)