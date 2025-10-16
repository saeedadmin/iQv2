#!/usr/bin/env python3
"""
Simple Apify test with manual status checking
"""

from apify_client import ApifyClient
import time
import json

def simple_apify_test():
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    print("🚀 Simple Apify test...")
    
    # Let's try the simplest possible actor first - web scraper
    run_input = {
        "startUrls": [{"url": "https://t.me/s/Shervin_Trading"}],
        "maxItems": 5,
        "proxyConfiguration": {"useApifyProxy": True}
    }
    
    try:
        print("⏳ Starting web scraper actor...")
        run = client.actor("apify/web-scraper").start(run_input=run_input)
        
        print(f"✅ Actor started! Run ID: {run['id']}")
        
        # Wait for a short time
        print("⏳ Waiting 30 seconds...")
        time.sleep(30)
        
        # Check status
        run_info = client.run(run['id']).get()
        print(f"📊 Status: {run_info['status']}")
        
        if run_info['status'] == 'SUCCEEDED':
            print("✅ Completed successfully!")
            
            # Get results
            dataset_items = client.dataset(run_info['defaultDatasetId']).list_items().items
            print(f"📊 Items found: {len(dataset_items)}")
            
            # Save results
            with open('/workspace/simple_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(dataset_items, f, ensure_ascii=False, indent=2)
            
            print("💾 Results saved to simple_test_results.json")
            
            # Show usage
            stats = run_info.get('stats', {})
            print(f"💰 Usage: {stats.get('computeUnits', 'N/A')} compute units")
            
            return dataset_items
            
        elif run_info['status'] == 'RUNNING':
            print("⏳ Still running... Let's wait more")
            
            # Wait another 60 seconds
            time.sleep(60)
            
            run_info = client.run(run['id']).get()
            print(f"📊 New status: {run_info['status']}")
            
            if run_info['status'] == 'SUCCEEDED':
                dataset_items = client.dataset(run_info['defaultDatasetId']).list_items().items
                print(f"✅ Finally completed! Items: {len(dataset_items)}")
                return dataset_items
            else:
                print(f"❌ Not completed yet: {run_info['status']}")
                return None
        else:
            print(f"❌ Failed with status: {run_info['status']}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    results = simple_apify_test()
    
    if results:
        print(f"\n🎉 Success! Got {len(results)} items")
        if results:
            print("\n📝 First item preview:")
            for key, value in list(results[0].items())[:5]:
                print(f"   {key}: {str(value)[:100]}...")
    else:
        print("\n❌ Test failed or no results")