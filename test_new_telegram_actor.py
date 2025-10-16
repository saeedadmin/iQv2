from apify_client import ApifyClient
import json
import time

# Initialize the ApifyClient with API token
client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")

print("🚀 Testing tri_angle/telegram-scraper...")

# Prepare Actor input
run_input = {
    "collectMessages": True,
    "profiles": ["telegram"],  # Using the official Telegram channel
    "scrapeLastNDays": 7  # Last 7 days to get recent messages
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
    print("📋 SAMPLE RESULTS:")
    print("="*60)
    
    # Show first few results
    for i, result in enumerate(results[:3]):  # Show first 3 items
        print(f"\n🔸 Item {i+1}:")
        print(f"   Username: {result.get('username', 'N/A')}")
        print(f"   Full Name: {result.get('fullName', 'N/A')}")
        print(f"   Followers: {result.get('followers', 'N/A')}")
        print(f"   Bio: {result.get('bio', 'N/A')[:100]}...")
        
        if result.get('message'):
            msg = result['message']
            print(f"   📨 Message Date: {msg.get('date', 'N/A')}")
            print(f"   📨 Message Views: {msg.get('views', 'N/A')}")
            print(f"   📨 Message Text: {msg.get('description', 'N/A')[:150]}...")
            print(f"   📨 Message Link: {msg.get('link', 'N/A')}")
        else:
            print("   📨 No message data")
        print("-" * 40)
    
    if len(results) > 3:
        print(f"... and {len(results) - 3} more results")
        
    print(f"\n✅ SUCCESS: Got {len(results)} items from @telegram channel!")
else:
    print("❌ No results found")

# Save results to file for inspection
with open('/workspace/telegram_scraper_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n💾 Full results saved to: telegram_scraper_results.json")