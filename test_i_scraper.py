#!/usr/bin/env python3
"""
Test i-scraper/telegram-channels-scraper as alternative
"""

from apify_client import ApifyClient
from datetime import datetime, timedelta
import json

def test_i_scraper():
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    print("🚀 Testing i-scraper/telegram-channels-scraper...")
    print(f"📊 Target: @Shervin_Trading")
    print("-" * 50)
    
    # Calculate date range (last 24 hours to get recent messages)
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=24)
    
    # Prepare input for i-scraper
    run_input = {
        "channels": ["@Shervin_Trading"],
        "dateFrom": start_date.strftime("%Y-%m-%d"),
        "dateTo": end_date.strftime("%Y-%m-%d"),
        "proxyConfiguration": {"useApifyProxy": True}
    }
    
    print(f"📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"🔧 Input: {run_input}")
    
    try:
        # Run the i-scraper Actor
        print("⏳ Running i-scraper Actor...")
        run = client.actor("i-scraper/telegram-channels-scraper").call(run_input=run_input)
        
        print(f"✅ Actor run completed!")
        print(f"🆔 Run ID: {run['id']}")
        print(f"📊 Status: {run['status']}")
        
        # Get the run details for cost analysis
        run_info = client.run(run['id']).get()
        print(f"💰 Usage stats:")
        print(f"   - Started at: {run_info.get('startedAt', 'N/A')}")
        print(f"   - Finished at: {run_info.get('finishedAt', 'N/A')}")
        print(f"   - Duration: {run_info.get('stats', {}).get('runTimeSecs', 'N/A')} seconds")
        print(f"   - Compute units used: {run_info.get('stats', {}).get('computeUnits', 'N/A')}")
        
        # Fetch and display the Dataset
        print("\n📋 Fetching results...")
        dataset_items = client.dataset(run['defaultDatasetId']).list_items().items
        
        print(f"📊 Total messages found: {len(dataset_items)}")
        
        if dataset_items:
            # Save full results to file
            with open('/workspace/i_scraper_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(dataset_items, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Full results saved to: i_scraper_test_results.json")
            
            # Display first few results
            print("\n🔍 Sample results (first 3 messages):")
            print("=" * 60)
            
            for i, item in enumerate(dataset_items[:3]):
                print(f"\n📝 Message {i+1}:")
                for key, value in item.items():
                    if key == 'text' and len(str(value)) > 150:
                        print(f"   {key}: {str(value)[:150]}...")
                    else:
                        print(f"   {key}: {value}")
        else:
            print("⚠️ No messages found in the specified date range")
            
        return dataset_items, run_info
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        
        # If i-scraper also fails, let's try another popular one
        print("\n🔄 Trying alternative approach with different actor...")
        
        try:
            # Let's try a simpler input structure
            simple_input = {
                "startUrls": [{"url": "https://t.me/s/Shervin_Trading"}],
                "maxItems": 5
            }
            
            print(f"🧪 Testing with simple input: {simple_input}")
            
            # Try a different scraper
            run2 = client.actor("drobnikj/telegram-scraper").start(run_input=simple_input)
            print(f"✅ Started alternative scraper! Run ID: {run2['id']}")
            
            # Wait a bit and check status
            completed = client.run(run2['id']).wait_for_finish(timeout_secs=120)
            
            if completed['status'] == 'SUCCEEDED':
                print("✅ Alternative scraper succeeded!")
                alt_results = client.dataset(completed['defaultDatasetId']).list_items().items
                print(f"📊 Alternative results count: {len(alt_results)}")
                return alt_results, completed
            else:
                print(f"❌ Alternative also failed: {completed['status']}")
                
        except Exception as e2:
            print(f"❌ Alternative also failed: {str(e2)}")
        
        return None, None

if __name__ == "__main__":
    results, run_info = test_i_scraper()
    
    if results:
        print(f"\n✅ Test completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Messages retrieved: {len(results)}")
        print(f"   - Channel: @Shervin_Trading")
        print(f"   - Cost: {run_info.get('stats', {}).get('computeUnits', 'N/A')} compute units")
    else:
        print("❌ All tests failed!")