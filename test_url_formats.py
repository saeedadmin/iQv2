#!/usr/bin/env python3
"""
Test different URL formats for pamnard/telegram-channels-scraper
"""

from apify_client import ApifyClient

def test_different_url_formats():
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    # Different URL formats to try
    url_formats = [
        "https://t.me/Shervin_Trading",
        "https://t.me/s/Shervin_Trading", 
        "https://web.telegram.org/z/#Shervin_Trading",
        "https://telegram.me/Shervin_Trading",
        "t.me/Shervin_Trading",
        "telegram.me/Shervin_Trading",
        "@Shervin_Trading",
        "Shervin_Trading"
    ]
    
    for i, url_format in enumerate(url_formats, 1):
        print(f"\n🧪 Test {i}: Trying URL format: {url_format}")
        
        test_input = {
            "channels": [url_format],
            "messagesLimit": 5
        }
        
        try:
            # Use start() instead of call() to get immediate response without waiting
            run = client.actor("pamnard/telegram-channels-scraper").start(run_input=test_input)
            print(f"✅ SUCCESS! URL format '{url_format}' was accepted!")
            print(f"🆔 Run ID: {run['id']}")
            
            # Wait for completion 
            print("⏳ Waiting for completion...")
            completed_run = client.run(run['id']).wait_for_finish()
            
            if completed_run['status'] == 'SUCCEEDED':
                print("✅ Run completed successfully!")
                
                # Get results
                dataset_items = client.dataset(completed_run['defaultDatasetId']).list_items().items
                print(f"📊 Messages found: {len(dataset_items)}")
                
                # Get usage stats
                run_info = client.run(run['id']).get()
                print(f"💰 Usage stats:")
                print(f"   - Compute units used: {run_info.get('stats', {}).get('computeUnits', 'N/A')}")
                print(f"   - Duration: {run_info.get('stats', {}).get('runTimeSecs', 'N/A')} seconds")
                
                return url_format, dataset_items, run_info
            else:
                print(f"❌ Run failed with status: {completed_run['status']}")
                
        except Exception as e:
            error_msg = str(e)
            if "do not contain valid URLs" in error_msg:
                print(f"❌ Invalid URL format")
            elif "Field input.channels is required" in error_msg:
                print(f"❌ Missing channels field")
            else:
                print(f"❌ Error: {error_msg}")
    
    return None, None, None

if __name__ == "__main__":
    success_format, results, run_info = test_different_url_formats()
    
    if success_format:
        print(f"\n🎉 SUCCESS! Working URL format: {success_format}")
        print(f"📊 Total messages: {len(results)}")
    else:
        print(f"\n❌ None of the URL formats worked!")
        print(f"💡 This actor might have specific requirements or be broken.")