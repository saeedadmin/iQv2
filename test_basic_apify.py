#!/usr/bin/env python3
"""
Test basic Apify functionality with a known working actor
"""

from apify_client import ApifyClient
import json

def test_basic_functionality():
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    print("🚀 Testing basic Apify functionality...")
    
    # First, let's check our account status
    try:
        user_info = client.user('me').get()
        print(f"👤 Account: {user_info.get('username', 'N/A')}")
        print(f"💰 Monthly usage: ${user_info.get('monthlyChargedUsd', 0)}")
        print(f"🆔 User ID: {user_info.get('id', 'N/A')}")
    except Exception as e:
        print(f"⚠️ Couldn't get user info: {e}")
    
    # Try a simple working actor - the crawler
    run_input = {
        "startUrls": [
            {"url": "https://t.me/s/Shervin_Trading"}
        ],
        "maxRequestsPerCrawl": 5,
        "requestTimeoutSecs": 30
    }
    
    try:
        print("\n⏳ Testing with crawlee-cheerio-crawler...")
        run = client.actor("crawlee/cheerio-crawler").call(run_input=run_input, timeout_secs=120)
        
        print(f"✅ Success! Run ID: {run['id']}")
        print(f"📊 Status: {run['status']}")
        
        # Get usage stats
        run_info = client.run(run['id']).get()
        stats = run_info.get('stats', {})
        print(f"💰 Cost: {stats.get('computeUnits', 'N/A')} compute units")
        print(f"⏱️ Duration: {stats.get('runTimeSecs', 'N/A')} seconds")
        
        # Get results
        dataset_items = client.dataset(run['defaultDatasetId']).list_items().items
        print(f"📊 Items scraped: {len(dataset_items)}")
        
        if dataset_items:
            # Save results
            with open('/workspace/crawlee_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(dataset_items, f, ensure_ascii=False, indent=2)
            
            print("💾 Results saved to crawlee_test_results.json")
            
            # Show sample
            print("\n📝 Sample result:")
            sample = dataset_items[0]
            for key, value in list(sample.items())[:3]:
                print(f"   {key}: {str(value)[:150]}...")
                
            return True
        else:
            print("⚠️ No results found")
            return False
            
    except Exception as e:
        print(f"❌ Crawler test failed: {str(e)}")
        
        # If that fails, let's try something even simpler
        print("\n🔄 Trying alternative simple test...")
        
        try:
            # Try getting our runs to see if API works at all
            my_runs = client.runs().list(limit=5).items
            print(f"✅ API connection works! Found {len(my_runs)} recent runs")
            
            if my_runs:
                print("📋 Recent runs:")
                for run in my_runs[:3]:
                    print(f"   - {run['id']}: {run['status']} ({run.get('actorId', 'N/A')})")
                    
            return True
            
        except Exception as e2:
            print(f"❌ Even basic API call failed: {str(e2)}")
            return False

if __name__ == "__main__":
    success = test_basic_functionality()
    
    if success:
        print("\n🎉 Apify API is working!")
    else:
        print("\n❌ Apify API connection failed")