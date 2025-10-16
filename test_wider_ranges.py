#!/usr/bin/env python3
"""
Test @Shervin_Trading with wider date ranges
"""

from apify_client import ApifyClient
import json
from datetime import datetime, timedelta

def test_wider_date_ranges():
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    print("🎯 Testing @Shervin_Trading with wider date ranges")
    print("=" * 60)
    
    # Different date ranges to try
    today = datetime.now()
    
    date_ranges = [
        {
            "name": "Last 7 days",
            "from": (today - timedelta(days=7)).strftime("%Y-%m-%d"),
            "to": today.strftime("%Y-%m-%d")
        },
        {
            "name": "Last 2 weeks", 
            "from": (today - timedelta(days=14)).strftime("%Y-%m-%d"),
            "to": today.strftime("%Y-%m-%d")
        },
        {
            "name": "Last month",
            "from": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
            "to": today.strftime("%Y-%m-%d")
        }
    ]
    
    for i, date_range in enumerate(date_ranges, 1):
        print(f"\n🧪 Test {i}: {date_range['name']}")
        print(f"📅 Date range: {date_range['from']} to {date_range['to']}")
        
        # Test input
        test_input = {
            "channels": ["@Shervin_Trading"],
            "dateFrom": date_range['from'],
            "dateTo": date_range['to'],
            "proxyConfiguration": {"useApifyProxy": True}
        }
        
        try:
            # Start the run
            run = client.actor("i-scraper/telegram-channels-scraper").start(run_input=test_input)
            print(f"   🚀 Started run: {run['id']}")
            
            # Wait for completion with longer timeout for wider ranges
            import time
            max_wait = 180  # 3 minutes for wider ranges
            wait_interval = 20
            waited = 0
            
            while waited < max_wait:
                time.sleep(wait_interval)
                waited += wait_interval
                
                run_status = client.run(run['id']).get()
                status = run_status['status']
                
                print(f"   📊 Status after {waited}s: {status}")
                
                if status == 'SUCCEEDED':
                    print(f"   ✅ SUCCESS!")
                    
                    # Get results
                    dataset_items = client.dataset(run_status['defaultDatasetId']).list_items().items
                    print(f"   📊 Messages found: {len(dataset_items)}")
                    
                    # Get cost
                    stats = run_status.get('stats', {})
                    compute_units = stats.get('computeUnits', 0)
                    duration = stats.get('runTimeSecs', 0)
                    
                    print(f"   💰 Cost: {compute_units:.4f} compute units")
                    print(f"   ⏱️ Duration: {duration} seconds")
                    print(f"   💵 USD: ${compute_units * 0.25:.4f}")
                    
                    if dataset_items:
                        # Save results
                        filename = f"/workspace/shervin_trading_results_{date_range['name'].replace(' ', '_').lower()}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(dataset_items, f, ensure_ascii=False, indent=2)
                        
                        print(f"   💾 Results saved: {filename}")
                        
                        # Show sample results
                        print(f"\n   📝 Sample Messages (first 3):")
                        for j, item in enumerate(dataset_items[:3]):
                            print(f"   📋 Message {j+1}:")
                            for key, value in item.items():
                                if key == 'text' and len(str(value)) > 120:
                                    print(f"      {key}: {str(value)[:120]}...")
                                elif key == 'date':
                                    print(f"      {key}: {value}")
                                elif key in ['channelName', 'authorName', 'id']:
                                    print(f"      {key}: {value}")
                        
                        # This was successful, return the results
                        print(f"\n🎉 SUCCESS! Found {len(dataset_items)} messages in {date_range['name']}")
                        return True, dataset_items, run_status, date_range
                    else:
                        print(f"   ⚠️ No messages found in {date_range['name']}")
                        break
                        
                elif status == 'FAILED':
                    print(f"   ❌ Run failed")
                    if 'statusMessage' in run_status:
                        print(f"   💬 Error: {run_status['statusMessage']}")
                    break
                    
                elif status not in ['RUNNING', 'READY']:
                    print(f"   ⚠️ Unexpected status: {status}")
                    break
            
            if waited >= max_wait:
                print(f"   ⏰ Timeout after {max_wait} seconds")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    return False, None, None, None

def get_account_usage():
    """Check current account usage"""
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    try:
        user_info = client.user('me').get()
        monthly_usage = user_info.get('monthlyChargedUsd', 0)
        print(f"💰 Current monthly usage: ${monthly_usage}")
        print(f"💳 Remaining free credit: ${5 - monthly_usage:.2f}")
        return 5 - monthly_usage
    except:
        return 5  # Assume full credit if can't check

if __name__ == "__main__":
    # Check remaining credit first
    remaining_credit = get_account_usage()
    
    if remaining_credit < 0.5:
        print("⚠️ Low free credit remaining. Consider upgrading or waiting for next month.")
    else:
        print(f"✅ Sufficient credit available: ${remaining_credit:.2f}")
    
    # Run the tests
    success, results, run_info, successful_range = test_wider_date_ranges()
    
    if success:
        print(f"\n🎉 FINAL SUCCESS!")
        print(f"📊 Messages retrieved: {len(results)}")
        print(f"📅 Successful range: {successful_range['name']}")
        print(f"💰 Cost: {run_info.get('stats', {}).get('computeUnits', 0):.4f} compute units")
        print(f"💵 USD cost: ${run_info.get('stats', {}).get('computeUnits', 0) * 0.25:.4f}")
        
        # Show summary
        print(f"\n📋 SUMMARY:")
        print(f"✅ Successfully scraped @Shervin_Trading")
        print(f"🎯 Working Actor: i-scraper/telegram-channels-scraper")
        print(f"📊 Messages: {len(results)}")
        print(f"📅 Date range: {successful_range['from']} to {successful_range['to']}")
        print(f"💰 Final cost: ~${run_info.get('stats', {}).get('computeUnits', 0) * 0.25:.4f}")
        
        # Check if we have trading signals
        trading_signals = []
        for msg in results[:5]:
            text = msg.get('text', '').lower()
            if any(word in text for word in ['buy', 'sell', 'signal', 'entry', 'target', 'stop']):
                trading_signals.append(msg)
        
        if trading_signals:
            print(f"\n📈 Found {len(trading_signals)} potential trading signals!")
            
    else:
        print(f"\n❌ No messages found in any date range")
        print(f"💡 Possible reasons:")
        print(f"   - Channel may be private/restricted")
        print(f"   - Channel name might be different")
        print(f"   - No recent activity in the channel")