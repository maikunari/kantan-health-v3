#!/usr/bin/env python3
"""
Anthropic Usage Tracking
Gets actual usage data from Anthropic API
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class AnthropicUsageTracker:
    """Track actual Anthropic API usage and costs"""
    
    # Pricing as of Jan 2025 (per million tokens)
    PRICING = {
        "claude-3-7-sonnet-20250219": {
            "input": 3.00,   # $3 per million input tokens
            "output": 15.00  # $15 per million output tokens
        },
        "claude-3-5-sonnet-20241022": {
            "input": 3.00,
            "output": 15.00
        },
        "claude-3-haiku-20240307": {
            "input": 0.25,
            "output": 1.25
        },
        "claude-3-opus-20240229": {
            "input": 15.00,
            "output": 75.00
        }
    }
    
    def __init__(self):
        """Initialize with Anthropic API key"""
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not set")
            return
        
        # Note: Anthropic doesn't currently have a billing API endpoint
        # We track usage locally and calculate costs
        self.usage_log_file = "logs/anthropic_usage.json"
        
    def track_usage(self, model: str, input_tokens: int, output_tokens: int):
        """Track usage after each API call
        
        Args:
            model: Model name used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        
        # Calculate cost
        pricing = self.PRICING.get(model, self.PRICING["claude-3-haiku-20240307"])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        # Log to file
        usage_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 4),
            "output_cost": round(output_cost, 4),
            "total_cost": round(total_cost, 4)
        }
        
        # Append to log file
        import json
        try:
            if os.path.exists(self.usage_log_file):
                with open(self.usage_log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(usage_entry)
            
            with open(self.usage_log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging usage: {e}")
        
        return total_cost
    
    def get_daily_usage(self, date: Optional[datetime] = None) -> Dict:
        """Get usage for a specific day
        
        Args:
            date: Date to get usage for (default: today)
            
        Returns:
            Dict with usage statistics
        """
        if not date:
            date = datetime.now()
        
        date_str = date.strftime('%Y-%m-%d')
        
        try:
            import json
            if not os.path.exists(self.usage_log_file):
                return {"date": date_str, "total_cost": 0, "requests": 0}
            
            with open(self.usage_log_file, 'r') as f:
                logs = json.load(f)
            
            daily_stats = {
                "date": date_str,
                "total_cost": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "requests": 0,
                "by_model": {}
            }
            
            for entry in logs:
                entry_date = datetime.fromisoformat(entry["timestamp"]).strftime('%Y-%m-%d')
                if entry_date == date_str:
                    daily_stats["total_cost"] += entry["total_cost"]
                    daily_stats["total_input_tokens"] += entry["input_tokens"]
                    daily_stats["total_output_tokens"] += entry["output_tokens"]
                    daily_stats["requests"] += 1
                    
                    model = entry["model"]
                    if model not in daily_stats["by_model"]:
                        daily_stats["by_model"][model] = {
                            "requests": 0,
                            "cost": 0,
                            "input_tokens": 0,
                            "output_tokens": 0
                        }
                    
                    daily_stats["by_model"][model]["requests"] += 1
                    daily_stats["by_model"][model]["cost"] += entry["total_cost"]
                    daily_stats["by_model"][model]["input_tokens"] += entry["input_tokens"]
                    daily_stats["by_model"][model]["output_tokens"] += entry["output_tokens"]
            
            return daily_stats
            
        except Exception as e:
            logger.error(f"Error getting daily usage: {e}")
            return {"error": str(e)}
    
    def get_monthly_usage(self) -> Dict:
        """Get usage for current month"""
        
        today = datetime.now()
        first_of_month = datetime(today.year, today.month, 1)
        
        monthly_stats = {
            "month": today.strftime('%Y-%m'),
            "total_cost": 0,
            "total_requests": 0,
            "by_model": {},
            "daily_breakdown": []
        }
        
        current = first_of_month
        while current <= today:
            daily = self.get_daily_usage(current)
            if "total_cost" in daily:
                monthly_stats["total_cost"] += daily["total_cost"]
                monthly_stats["total_requests"] += daily.get("requests", 0)
                monthly_stats["daily_breakdown"].append(daily)
            current += timedelta(days=1)
        
        return monthly_stats


class AnthropicAPIUsage:
    """
    Alternative: Parse Anthropic API responses for usage data
    This can be integrated into the content generator
    """
    
    @staticmethod
    def extract_usage_from_response(response) -> Dict:
        """Extract usage data from Anthropic API response
        
        Args:
            response: Response from anthropic.messages.create()
            
        Returns:
            Dict with token counts
        """
        try:
            # Anthropic returns usage in the response
            usage = {
                "input_tokens": response.usage.input_tokens if hasattr(response, 'usage') else 0,
                "output_tokens": response.usage.output_tokens if hasattr(response, 'usage') else 0,
                "model": response.model if hasattr(response, 'model') else "unknown"
            }
            return usage
        except Exception as e:
            logger.error(f"Error extracting usage: {e}")
            return {"input_tokens": 0, "output_tokens": 0}


def integrate_with_content_generator():
    """
    Example of how to integrate with your content generator
    """
    
    print("""
    ============================================================
    ANTHROPIC USAGE TRACKING INTEGRATION
    ============================================================
    
    To track actual Anthropic costs, update your content generator:
    
    1. In generate_taxonomy_content.py, after each API call:
    
    ```python
    response = self.client.messages.create(...)
    
    # Track usage
    from src.processors.anthropic_usage import AnthropicUsageTracker, AnthropicAPIUsage
    
    usage = AnthropicAPIUsage.extract_usage_from_response(response)
    tracker = AnthropicUsageTracker()
    cost = tracker.track_usage(
        model="claude-3-7-sonnet-20250219",
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"]
    )
    
    logger.info(f"API call cost: ${cost:.4f}")
    ```
    
    2. View usage in dashboard:
    
    ```python
    tracker = AnthropicUsageTracker()
    daily = tracker.get_daily_usage()
    monthly = tracker.get_monthly_usage()
    
    print(f"Today's Anthropic costs: ${daily['total_cost']:.2f}")
    print(f"Monthly Anthropic costs: ${monthly['total_cost']:.2f}")
    ```
    
    ============================================================
    """)


if __name__ == "__main__":
    # Test the usage tracker
    tracker = AnthropicUsageTracker()
    
    # Simulate tracking a call
    cost = tracker.track_usage(
        model="claude-3-7-sonnet-20250219",
        input_tokens=1000,
        output_tokens=2000
    )
    print(f"Sample call cost: ${cost:.4f}")
    
    # Get today's usage
    daily = tracker.get_daily_usage()
    print(f"Today's usage: {daily}")
    
    # Get monthly usage
    monthly = tracker.get_monthly_usage()
    print(f"Monthly usage: {monthly}")