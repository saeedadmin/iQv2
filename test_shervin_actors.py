#!/usr/bin/env python3
"""
Try to replicate the successful format with Shervin_Trading channel
"""

from apify_client import ApifyClient
import json
import time

def test_telegram_actors_for_shervin():
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    print("🎯 Testing Telegram actors for @Shervin_Trading...")
    
    # Popular Telegram scrapers to try
    actors_to_test = [
        ("jirimoravcik/telegram-posts-scraper", {
            "telegram_channels": ["@Shervin_Trading"],
            "max_posts": 5
        }),
        ("lukaskrivka/telegram-scraper", {
            "startUrls": ["https://t.me/s/Shervin_Trading"],
            "maxItems": 5
        }),
        ("epctex/telegram-scraper", {
            "channels": ["@Shervin_Trading"],
            "numberOfPosts": 5
        }),
        ("trilom/telegram-history-scraper", {
            "channels": ["@Shervin_Trading"],
            "limit": 5
        })
    ]
    
    for actor_name, input_data in actors_to_test:
        print(f"\n🧪 Testing: {actor_name}")
        print(f"📥 Input: {input_data}")
        
        try:
            # Check if actor exists
            actor_info = client.actor(actor_name).get()
            print(f"   ✅ Actor found: {actor_info.get('title', 'N/A')}")
            
            # Start the run
            run = client.actor(actor_name).start(run_input=input_data)
            print(f"   🚀 Started run: {run['id']}")
            
            # Wait a bit for it to start
            time.sleep(10)
            
            # Check status
            run_status = client.run(run['id']).get()
            print(f"   📊 Status: {run_status['status']}")
            
            if run_status['status'] == 'RUNNING':
                print(f"   ⏳ Still running... waiting 60 seconds")
                time.sleep(60)
                
                # Check again
                final_status = client.run(run['id']).get()
                print(f"   📊 Final status: {final_status['status']}")
                
                if final_status['status'] == 'SUCCEEDED':
                    print(f"   ✅ SUCCESS!")
                    
                    # Get results
                    dataset_items = client.dataset(final_status['defaultDatasetId']).list_items().items
                    print(f"   📊 Items found: {len(dataset_items)}")
                    
                    if dataset_items:
                        # Save results
                        filename = f"/workspace/{actor_name.replace('/', '_')}_shervin_results.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(dataset_items, f, ensure_ascii=False, indent=2)
                        
                        print(f"   💾 Results saved: {filename}")
                        
                        # Show sample
                        print(f"   📝 Sample result keys: {list(dataset_items[0].keys())}")
                        if 'text' in dataset_items[0]:
                            print(f"   📄 Sample text: {dataset_items[0]['text'][:100]}...")
                        
                        # Show cost
                        stats = final_status.get('stats', {})
                        print(f"   💰 Cost: {stats.get('computeUnits', 'N/A')} compute units")
                        
                        return actor_name, dataset_items, final_status
            
            elif run_status['status'] == 'SUCCEEDED':
                print(f"   ✅ Quick success!")
                # Handle immediate success...
                dataset_items = client.dataset(run_status['defaultDatasetId']).list_items().items
                print(f"   📊 Items: {len(dataset_items)}")
                return actor_name, dataset_items, run_status
                
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                print(f"   ❌ Actor not found")
            elif "not valid" in error_msg.lower():
                print(f"   ❌ Invalid input: {error_msg[:100]}...")
            else:
                print(f"   ❌ Error: {error_msg[:100]}...")
    
    # If none of the specific actors work, let's try a more generic approach
    print(f"\n🔄 Trying generic web scraper approach...")
    
    try:
        generic_input = {
            "startUrls": [{"url": "https://t.me/s/Shervin_Trading"}],
            "maxRequestsPerCrawl": 5,
            "requestTimeoutSecs": 30,
            "outputFormat": "json"
        }
        
        # Try popular generic scrapers
        generic_actors = [
            "apify/cheerio-scraper",
            "apify/web-scraper"
        ]
        
        for generic_actor in generic_actors:
            print(f"   🧪 Trying {generic_actor}...")
            
            try:
                run = client.actor(generic_actor).start(run_input=generic_input)
                print(f"   🚀 Started: {run['id']}")
                
                # Don't wait too long for generic ones
                time.sleep(30)
                
                status = client.run(run['id']).get()
                
                if status['status'] == 'SUCCEEDED':
                    results = client.dataset(status['defaultDatasetId']).list_items().items
                    print(f"   ✅ {generic_actor} succeeded with {len(results)} items")
                    
                    if results:
                        return generic_actor, results, status
                        
            except Exception as e:
                print(f"   ❌ {generic_actor} failed: {str(e)[:50]}...")
    
    except Exception as e:
        print(f"❌ Generic approach failed: {str(e)}")
    
    return None, None, None

if __name__ == "__main__":
    success_actor, results, run_info = test_telegram_actors_for_shervin()
    
    if success_actor:
        print(f"\n🎉 SUCCESS!")
        print(f"🏆 Working actor: {success_actor}")
        print(f"📊 Results: {len(results)} items")
        print(f"💰 Cost: {run_info.get('stats', {}).get('computeUnits', 'N/A')} compute units")
    else:
        print(f"\n❌ No actors worked for @Shervin_Trading")
        print(f"💡 We may need to try different input formats or actors")