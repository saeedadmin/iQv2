#!/usr/bin/env python3
"""
Check Apify Actor input schema for pamnard/telegram-channels-scraper
"""

from apify_client import ApifyClient

def check_actor_input_schema():
    # Initialize the ApifyClient
    client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")
    
    try:
        # Get actor information
        actor_info = client.actor("pamnard/telegram-channels-scraper").get()
        
        print("🔍 Actor Information:")
        print(f"   Name: {actor_info.get('name')}")
        print(f"   Title: {actor_info.get('title')}")
        print(f"   Description: {actor_info.get('description', 'N/A')[:200]}...")
        
        # Try to get input schema
        if 'inputSchema' in actor_info:
            print("\n📋 Input Schema:")
            print(actor_info['inputSchema'])
        else:
            print("\n❌ No input schema found")
            
        # Let's also try a basic input to see what error we get
        print("\n🧪 Testing basic input...")
        
        basic_input = {
            "channel": "Shervin_Trading"
        }
        
        print(f"Testing with: {basic_input}")
        
        try:
            run = client.actor("pamnard/telegram-channels-scraper").call(run_input=basic_input, timeout_secs=60)
            print("✅ Basic test succeeded!")
            return run
        except Exception as e:
            print(f"❌ Basic test error: {str(e)}")
            
            # Try another format
            print("\n🧪 Testing alternative format...")
            alt_input = {
                "channels": ["Shervin_Trading"],
                "limit": 5
            }
            print(f"Testing with: {alt_input}")
            
            try:
                run = client.actor("pamnard/telegram-channels-scraper").call(run_input=alt_input, timeout_secs=60)
                print("✅ Alternative test succeeded!")
                return run
            except Exception as e2:
                print(f"❌ Alternative test error: {str(e2)}")
                return None
        
    except Exception as e:
        print(f"❌ Error getting actor info: {str(e)}")
        return None

if __name__ == "__main__":
    check_actor_input_schema()