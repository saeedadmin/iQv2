#!/usr/bin/env python3
"""
Check status of the wider range test
"""

from apify_client import ApifyClient
import json

def check_wider_range_test():
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    run_id = "TqEuCNM2fO7nSdJtf"
    
    try:
        run_info = client.run(run_id).get()
        print(f"📊 Status: {run_info['status']}")
        
        if run_info['status'] == 'SUCCEEDED':
            print("✅ SUCCESS!")
            
            if run_info.get('defaultDatasetId'):
                items = client.dataset(run_info['defaultDatasetId']).list_items().items
                print(f"📊 Messages found: {len(items)}")
                
                if items:
                    # Save results
                    with open('/workspace/shervin_wider_results.json', 'w', encoding='utf-8') as f:
                        json.dump(items, f, ensure_ascii=False, indent=2)
                    
                    print("💾 Results saved to shervin_wider_results.json")
                    
                    # Show sample
                    sample = items[0]
                    print(f"🔍 Sample keys: {list(sample.keys())}")
                    print(f"🎯 Channel: {sample.get('channelName', 'N/A')}")
                    
                    if 'text' in sample:
                        text = sample['text']
                        print(f"📄 Sample text: {text[:150]}...")
                    
                    if 'date' in sample:
                        print(f"📅 Date: {sample['date']}")
                    
                    # Show detailed first few messages
                    print(f"\n📋 First 3 messages details:")
                    for i, item in enumerate(items[:3]):
                        print(f"\n📝 Message {i+1}:")
                        for key, value in item.items():
                            if key == 'text' and len(str(value)) > 120:
                                print(f"   {key}: {str(value)[:120]}...")
                            else:
                                print(f"   {key}: {value}")
                
                # Show cost
                stats = run_info.get('stats', {})
                compute_units = stats.get('computeUnits', 0)
                duration = stats.get('runTimeSecs', 0)
                
                print(f"\n💰 Cost Analysis:")
                print(f"   Compute units: {compute_units:.4f}")
                print(f"   Duration: {duration} seconds")
                print(f"   USD cost: ${compute_units * 0.25:.4f}")
                
                return len(items) if items else 0, compute_units
            else:
                print("❌ No dataset found")
                return 0, 0
                
        elif run_info['status'] == 'FAILED':
            print(f"❌ Run failed: {run_info.get('statusMessage', 'No error message')}")
            return 0, 0
        else:
            print(f"⏳ Still running... current status: {run_info['status']}")
            return None, 0
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 0, 0

if __name__ == "__main__":
    messages_count, cost = check_wider_range_test()
    
    if messages_count is not None:
        if messages_count > 0:
            print(f"\n🎉 FINAL RESULT:")
            print(f"✅ Successfully found {messages_count} messages from @Shervin_Trading")
            print(f"💰 Cost: ${cost * 0.25:.4f}")
            print(f"📅 Date range: Last 7 days (2025-10-10 to 2025-10-17)")
        else:
            print(f"\n❌ No messages found even with wider date range")
    else:
        print(f"\n⏳ Test still in progress...")