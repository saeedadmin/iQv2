#!/usr/bin/env python3
"""
Check successful runs and find working Telegram scrapers
"""

from apify_client import ApifyClient
import json

def check_successful_runs():
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    print("🔍 Checking previous successful runs...")
    
    try:
        # Get detailed info about successful runs
        my_runs = client.runs().list(limit=10).items
        
        successful_runs = [run for run in my_runs if run['status'] == 'SUCCEEDED']
        
        print(f"✅ Found {len(successful_runs)} successful runs:")
        
        for i, run in enumerate(successful_runs[:5]):
            print(f"\n📊 Run {i+1}:")
            print(f"   🆔 ID: {run['id']}")
            print(f"   🕐 Started: {run.get('startedAt', 'N/A')}")
            print(f"   ⚡ Actor ID: {run.get('actorId', 'N/A')}")
            
            # Get more details
            run_details = client.run(run['id']).get()
            stats = run_details.get('stats', {})
            
            print(f"   💰 Cost: {stats.get('computeUnits', 'N/A')} compute units")
            print(f"   ⏱️ Duration: {stats.get('runTimeSecs', 'N/A')} seconds")
            
            # Check if it has results
            if run_details.get('defaultDatasetId'):
                try:
                    items = client.dataset(run_details['defaultDatasetId']).list_items(limit=1).items
                    print(f"   📊 Results: {len(items)} items (sample check)")
                    
                    if items:
                        # Show sample result structure
                        sample = items[0]
                        print(f"   🔍 Sample keys: {list(sample.keys())[:5]}")
                        
                except:
                    print(f"   📊 Results: Unable to check")
        
        # Now let's try some known Telegram scrapers
        print(f"\n🧪 Testing known Telegram scrapers...")
        
        # List of potentially working Telegram scrapers
        telegram_actors = [
            "drobnikj/telegram-scraper", 
            "webfinity/telegram-scraper-v2",
            "jirimoravcik/telegram-posts-scraper"
        ]
        
        for actor_name in telegram_actors:
            print(f"\n🔬 Testing {actor_name}...")
            
            try:
                # Get actor info
                actor_info = client.actor(actor_name).get()
                print(f"   ✅ Found: {actor_info.get('title', 'N/A')}")
                print(f"   📝 Description: {actor_info.get('description', 'N/A')[:100]}...")
                
                # Try a simple test run
                simple_input = {
                    "startUrls": [{"url": "https://t.me/s/Shervin_Trading"}],
                    "maxItems": 3
                }
                
                print(f"   ⏳ Starting test run...")
                test_run = client.actor(actor_name).start(run_input=simple_input)
                
                print(f"   🚀 Started! Run ID: {test_run['id']}")
                
                # We'll check results separately to avoid timeouts
                return test_run['id'], actor_name
                
            except Exception as e:
                error_msg = str(e)
                if "not found" in error_msg.lower():
                    print(f"   ❌ Not found")
                else:
                    print(f"   ❌ Error: {error_msg[:100]}...")
        
        return None, None
        
    except Exception as e:
        print(f"❌ Error checking runs: {str(e)}")
        return None, None

def check_run_status(run_id, actor_name):
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    print(f"\n🔍 Checking status of {actor_name} run: {run_id}")
    
    try:
        run_info = client.run(run_id).get()
        print(f"📊 Status: {run_info['status']}")
        
        if run_info['status'] == 'SUCCEEDED':
            print("✅ Completed successfully!")
            
            # Get results
            if run_info.get('defaultDatasetId'):
                dataset_items = client.dataset(run_info['defaultDatasetId']).list_items().items
                print(f"📊 Items found: {len(dataset_items)}")
                
                if dataset_items:
                    # Save results
                    filename = f"/workspace/{actor_name.replace('/', '_')}_results.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(dataset_items, f, ensure_ascii=False, indent=2)
                    
                    print(f"💾 Results saved to: {filename}")
                    
                    # Show sample
                    print("\n📝 Sample result:")
                    sample = dataset_items[0]
                    for key, value in list(sample.items())[:5]:
                        print(f"   {key}: {str(value)[:100]}...")
                    
                    # Show usage
                    stats = run_info.get('stats', {})
                    print(f"\n💰 Usage:")
                    print(f"   - Compute units: {stats.get('computeUnits', 'N/A')}")
                    print(f"   - Duration: {stats.get('runTimeSecs', 'N/A')} seconds")
                    
                    return True
                    
        elif run_info['status'] == 'RUNNING':
            print("⏳ Still running...")
            return False
        else:
            print(f"❌ Failed with status: {run_info['status']}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking status: {str(e)}")
        return False

if __name__ == "__main__":
    run_id, actor_name = check_successful_runs()
    
    if run_id:
        print(f"\n⏱️ Waiting 30 seconds for run to complete...")
        import time
        time.sleep(30)
        
        success = check_run_status(run_id, actor_name)
        
        if success:
            print(f"\n🎉 Successfully tested {actor_name}!")
        else:
            print(f"\n⏳ Run may still be in progress. Check manually later.")
    else:
        print(f"\n❌ No working Telegram scrapers found")