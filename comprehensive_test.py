#!/usr/bin/env python3
"""
Final comprehensive test: wider range + test with known public channel
"""

from apify_client import ApifyClient
import json
from datetime import datetime, timedelta

def comprehensive_test():
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    print("🎯 Comprehensive Telegram scraping test")
    print("=" * 60)
    
    # Test 1: @Shervin_Trading with very wide range (2 months)
    today = datetime.now()
    two_months_ago = (today - timedelta(days=60)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")
    
    print(f"\n🧪 Test 1: @Shervin_Trading with 2-month range")
    print(f"📅 Date range: {two_months_ago} to {today_str}")
    
    shervin_input = {
        "channels": ["@Shervin_Trading"],
        "dateFrom": two_months_ago,
        "dateTo": today_str,
        "proxyConfiguration": {"useApifyProxy": True}
    }
    
    try:
        shervin_run = client.actor("i-scraper/telegram-channels-scraper").start(run_input=shervin_input)
        print(f"   🚀 Started Shervin run: {shervin_run['id']}")
    except Exception as e:
        print(f"   ❌ Failed to start Shervin test: {str(e)}")
        shervin_run = None
    
    # Test 2: Known public trading channel for validation
    print(f"\n🧪 Test 2: Public trading channel validation")
    
    # Try some well-known public trading channels
    public_channels = [
        "@bitcoincom",
        "@telegram", 
        "@durov"  # Telegram founder's channel - should definitely be public
    ]
    
    validation_results = []
    
    for channel in public_channels:
        print(f"\n   📡 Testing {channel}...")
        
        validation_input = {
            "channels": [channel],
            "dateFrom": (today - timedelta(days=7)).strftime("%Y-%m-%d"),
            "dateTo": today_str,
            "proxyConfiguration": {"useApifyProxy": True}
        }
        
        try:
            validation_run = client.actor("i-scraper/telegram-channels-scraper").start(run_input=validation_input)
            print(f"      🚀 Started validation run: {validation_run['id']}")
            validation_results.append((channel, validation_run['id']))
        except Exception as e:
            print(f"      ❌ Failed: {str(e)}")
    
    # Wait and check results
    print(f"\n⏳ Waiting for results (60 seconds)...")
    
    import time
    time.sleep(60)
    
    all_results = {}
    
    # Check Shervin results
    if shervin_run:
        print(f"\n📊 Checking @Shervin_Trading results...")
        try:
            shervin_status = client.run(shervin_run['id']).get()
            print(f"   Status: {shervin_status['status']}")
            
            if shervin_status['status'] == 'SUCCEEDED':
                if shervin_status.get('defaultDatasetId'):
                    shervin_items = client.dataset(shervin_status['defaultDatasetId']).list_items().items
                    print(f"   📊 Messages: {len(shervin_items)}")
                    
                    stats = shervin_status.get('stats', {})
                    print(f"   💰 Cost: {stats.get('computeUnits', 0):.4f} compute units")
                    
                    if shervin_items:
                        # Save Shervin results
                        with open('/workspace/shervin_final_results.json', 'w', encoding='utf-8') as f:
                            json.dump(shervin_items, f, ensure_ascii=False, indent=2)
                        
                        all_results['@Shervin_Trading'] = {
                            'messages': len(shervin_items),
                            'cost': stats.get('computeUnits', 0),
                            'sample': shervin_items[0] if shervin_items else None
                        }
            elif shervin_status['status'] == 'RUNNING':
                print(f"   ⏳ Still running...")
            else:
                print(f"   ❌ Failed or other status: {shervin_status['status']}")
                
        except Exception as e:
            print(f"   ❌ Error checking Shervin: {str(e)}")
    
    # Check validation results
    print(f"\n📊 Checking validation channel results...")
    
    for channel, run_id in validation_results:
        print(f"\n   📡 Checking {channel}...")
        try:
            val_status = client.run(run_id).get()
            print(f"      Status: {val_status['status']}")
            
            if val_status['status'] == 'SUCCEEDED':
                if val_status.get('defaultDatasetId'):
                    val_items = client.dataset(val_status['defaultDatasetId']).list_items().items
                    print(f"      📊 Messages: {len(val_items)}")
                    
                    if val_items:
                        all_results[channel] = {
                            'messages': len(val_items),
                            'cost': val_status.get('stats', {}).get('computeUnits', 0),
                            'sample': val_items[0]
                        }
                        
                        # Show sample for first successful validation
                        if len(all_results) == 1:
                            print(f"      📝 Sample message keys: {list(val_items[0].keys())}")
                            if 'text' in val_items[0]:
                                print(f"      📄 Sample text: {val_items[0]['text'][:100]}...")
            
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
    
    return all_results

if __name__ == "__main__":
    results = comprehensive_test()
    
    print(f"\n" + "="*60)
    print(f"📋 FINAL COMPREHENSIVE RESULTS")
    print(f"="*60)
    
    total_cost = 0
    
    if results:
        for channel, data in results.items():
            print(f"\n✅ {channel}:")
            print(f"   📊 Messages: {data['messages']}")
            print(f"   💰 Cost: {data['cost']:.4f} compute units")
            print(f"   💵 USD: ${data['cost'] * 0.25:.4f}")
            total_cost += data['cost']
            
            if data['sample']:
                print(f"   🔍 Sample keys: {list(data['sample'].keys())}")
    else:
        print(f"\n❌ No successful results from any channel")
    
    print(f"\n💰 Total cost: {total_cost:.4f} compute units (${total_cost * 0.25:.4f})")
    
    # Analysis
    if '@Shervin_Trading' in results and results['@Shervin_Trading']['messages'] > 0:
        print(f"\n🎉 SUCCESS: @Shervin_Trading is accessible and has messages!")
    elif any(data['messages'] > 0 for data in results.values()):
        print(f"\n⚠️ ANALYSIS: Other channels work, but @Shervin_Trading appears to be:")
        print(f"   - Private/restricted channel")
        print(f"   - No recent activity")
        print(f"   - Different channel name")
    else:
        print(f"\n❌ ANALYSIS: No channels returned messages - possible API or config issue")