#!/usr/bin/env python3
"""
Test script for pamnard/telegram-channels-scraper Apify Actor
"""

import json
from apify_client import ApifyClient

def test_telegram_scraper():
    # Initialize the ApifyClient with your API token
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    print("🚀 Starting Apify Telegram scraper test...")
    print(f"📊 Target: @Shervin_Trading")
    print(f"📝 Messages limit: 5")
    print("-" * 50)
    
    # Prepare the Actor input
    run_input = {
        "channels": ["https://t.me/Shervin_Trading"],
        "messagesLimit": 5,
        # Add other parameters if needed
        "proxyConfiguration": {"useApifyProxy": True}
    }
    
    try:
        # Run the Actor and wait for it to finish
        print("⏳ Running the actor...")
        run = client.actor("pamnard/telegram-channels-scraper").call(run_input=run_input)
        
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
        
        # Save full results to file
        with open('/workspace/apify_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(dataset_items, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Full results saved to: apify_test_results.json")
        
        # Display first few results
        print("\n🔍 Sample results (first 2 messages):")
        print("=" * 60)
        
        for i, item in enumerate(dataset_items[:2]):
            print(f"\n📝 Message {i+1}:")
            print(f"   📅 Date: {item.get('date', 'N/A')}")
            print(f"   ✍️  Text: {item.get('text', 'N/A')[:200]}...")
            print(f"   🔗 URL: {item.get('url', 'N/A')}")
            print(f"   👤 Author: {item.get('author', 'N/A')}")
            
        return dataset_items, run_info
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        return None, None

if __name__ == "__main__":
    results, run_info = test_telegram_scraper()
    
    if results:
        print(f"\n✅ Test completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Messages retrieved: {len(results)}")
        print(f"   - Actor: pamnard/telegram-channels-scraper")
        print(f"   - Channel: @Shervin_Trading")
    else:
        print("❌ Test failed!")