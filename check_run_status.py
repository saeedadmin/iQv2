#!/usr/bin/env python3
"""
Check status of recent runs manually
"""

from apify_client import ApifyClient
import json

def check_recent_runs():
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    print("🔍 Checking status of recent runs...")
    
    # Get recent runs
    recent_runs = client.runs().list(limit=5).items
    
    print(f"📊 Found {len(recent_runs)} recent runs:")
    print("=" * 60)
    
    for i, run in enumerate(recent_runs, 1):
        print(f"\n📋 Run {i}:")
        print(f"   🆔 ID: {run['id']}")
        print(f"   📊 Status: {run['status']}")
        print(f"   🕐 Started: {run.get('startedAt', 'N/A')}")
        print(f"   🏁 Finished: {run.get('finishedAt', 'N/A')}")
        
        # Get detailed info
        try:
            run_details = client.run(run['id']).get()
            
            # Show stats if available
            stats = run_details.get('stats', {})
            if stats:
                print(f"   💰 Cost: {stats.get('computeUnits', 'N/A')} compute units")
                print(f"   ⏱️ Duration: {stats.get('runTimeSecs', 'N/A')} seconds")
            
            # Check for results if succeeded
            if run['status'] == 'SUCCEEDED' and run_details.get('defaultDatasetId'):
                try:
                    dataset_items = client.dataset(run_details['defaultDatasetId']).list_items().items
                    print(f"   📊 Results: {len(dataset_items)} items")
                    
                    if dataset_items and len(dataset_items) > 0:
                        # Save results for the latest successful run
                        if i == 1:  # Most recent
                            filename = f"/workspace/latest_successful_results.json"
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(dataset_items, f, ensure_ascii=False, indent=2)
                            print(f"   💾 Results saved: {filename}")
                            
                            # Show sample
                            sample = dataset_items[0]
                            print(f"   🔍 Sample keys: {list(sample.keys())}")
                            
                            # Check if it's from Shervin_Trading
                            if 'channelName' in sample:
                                channel = sample.get('channelName', '')
                                print(f"   🎯 Channel: {channel}")
                                
                                if 'shervin' in channel.lower() or 'trading' in channel.lower():
                                    print("   ✅ SUCCESS! Found Shervin Trading data!")
                                    return True, dataset_items, run_details
                            
                            if 'text' in sample:
                                text_sample = sample['text'][:100]
                                print(f"   📄 Sample text: {text_sample}...")
                                
                except Exception as e:
                    print(f"   ❌ Error getting results: {str(e)}")
            
            elif run['status'] == 'FAILED':
                # Show error if available
                error_msg = run_details.get('statusMessage', 'No error message')
                print(f"   ❌ Error: {error_msg}")
                
        except Exception as e:
            print(f"   ⚠️ Error getting details: {str(e)}")
    
    return False, None, None

def check_specific_run(run_id):
    """Check a specific run by ID"""
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    print(f"\n🔍 Checking specific run: {run_id}")
    
    try:
        run_info = client.run(run_id).get()
        
        print(f"📊 Status: {run_info['status']}")
        
        if run_info['status'] == 'SUCCEEDED':
            print("✅ Run completed successfully!")
            
            # Get results
            if run_info.get('defaultDatasetId'):
                dataset_items = client.dataset(run_info['defaultDatasetId']).list_items().items
                print(f"📊 Items found: {len(dataset_items)}")
                
                if dataset_items:
                    # Save results
                    filename = f"/workspace/run_{run_id}_results.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(dataset_items, f, ensure_ascii=False, indent=2)
                    
                    print(f"💾 Results saved: {filename}")
                    
                    # Show usage
                    stats = run_info.get('stats', {})
                    print(f"💰 Cost: {stats.get('computeUnits', 'N/A')} compute units")
                    print(f"⏱️ Duration: {stats.get('runTimeSecs', 'N/A')} seconds")
                    
                    # Show sample
                    sample = dataset_items[0] if dataset_items else {}
                    print(f"📝 Sample result:")
                    for key, value in list(sample.items())[:5]:
                        if isinstance(value, str) and len(value) > 100:
                            print(f"   {key}: {value[:100]}...")
                        else:
                            print(f"   {key}: {value}")
                    
                    return True, dataset_items
                    
        elif run_info['status'] == 'RUNNING':
            print("⏳ Still running...")
            return False, None
        else:
            print(f"❌ Status: {run_info['status']}")
            if 'statusMessage' in run_info:
                print(f"💬 Message: {run_info['statusMessage']}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, None

if __name__ == "__main__":
    # Check recent runs
    success, results, run_info = check_recent_runs()
    
    if success:
        print(f"\n🎉 Found successful Shervin Trading results!")
    else:
        print(f"\n📋 Checking specific recent runs...")
        
        # Check the specific runs we started
        specific_runs = ["KEnZDSqd0Pbot0s93", "vbCKHnsLhQy8fj4Fc"]
        
        for run_id in specific_runs:
            success, results = check_specific_run(run_id)
            if success:
                print(f"\n🎉 Success with run {run_id}!")
                break