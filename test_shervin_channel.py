from apify_client import ApifyClient
import json
import time

# Initialize the ApifyClient with API token
client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")

print("🎯 Testing tri_angle/telegram-scraper on @Shervin_Trading...")

# Prepare Actor input for the target channel
run_input = {
    "collectMessages": True,
    "profiles": ["Shervin_Trading"],  # Target channel
    "scrapeLastNDays": 15  # Last 15 days to get more messages
}

print(f"📝 Input: {json.dumps(run_input, indent=2)}")

# Run the Actor and wait for it to finish
print("⏳ Starting actor run...")
run = client.actor("tri_angle/telegram-scraper").call(run_input=run_input)

print(f"✅ Actor run completed!")
print(f"📊 Run ID: {run['id']}")
print(f"🔗 Run URL: https://console.apify.com/view/runs/{run['id']}")

# Fetch the Actor results from the run's dataset
print("📥 Fetching results...")
results = []
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    results.append(item)

print(f"📈 Total results: {len(results)}")

if results:
    print("\n" + "="*60)
    print("📋 SHERVIN TRADING CHANNEL RESULTS:")
    print("="*60)
    
    # Show all results since it might be limited
    for i, result in enumerate(results):
        print(f"\n🔸 Item {i+1}:")
        print(f"   Username: {result.get('username', 'N/A')}")
        print(f"   Full Name: {result.get('fullName', 'N/A')}")
        print(f"   Followers: {result.get('followers', 'N/A'):,}")
        print(f"   Bio: {result.get('bio', 'N/A')[:100]}...")
        
        if result.get('message'):
            msg = result['message']
            print(f"   📨 Message Date: {msg.get('date', 'N/A')}")
            print(f"   📨 Message Full Date: {msg.get('fulldate', 'N/A')}")
            print(f"   📨 Message Views: {msg.get('views', 'N/A'):,}")
            print(f"   📨 Message Text: {msg.get('description', 'N/A')[:200]}...")
            print(f"   📨 Message Link: {msg.get('link', 'N/A')}")
            if msg.get('image'):
                print(f"   📨 Has Image: ✅")
            if msg.get('video'):
                print(f"   📨 Has Video: ✅")
        else:
            print("   📨 No message data")
        print("-" * 40)
        
    print(f"\n✅ SUCCESS: Got {len(results)} items from @Shervin_Trading channel!")
    
    # Save results to file for inspection
    with open('/workspace/shervin_trading_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Results saved to: shervin_trading_results.json")
else:
    print("❌ No results found for @Shervin_Trading")
    print("🔍 This could mean:")
    print("   - Channel is private/restricted")
    print("   - No messages in the last 15 days")
    print("   - Channel name might be different")
    print("   - Channel might be inactive")