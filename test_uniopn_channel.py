from apify_client import ApifyClient
import json
from datetime import datetime

# Initialize the ApifyClient with API token
client = ApifyClient("apify_api_TlFKaUvvz0nTU5B13YdisQHTrcr08L1L7IKc")

print("🎯 Testing @uniopn channel...")

# Prepare Actor input for uniopn channel
run_input = {
    "collectMessages": True,
    "profiles": ["uniopn"],
    "scrapeLastNDays": 7  # Last 7 days
}

print(f"📝 Input: {json.dumps(run_input, indent=2)}")

# Run the Actor and wait for it to finish
print("⏳ Starting actor run...")
run = client.actor("tri_angle/telegram-scraper").call(run_input=run_input)

print(f"✅ Actor run completed!")

# Fetch the Actor results from the run's dataset
print("📥 Fetching results...")
results = []
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    results.append(item)

print(f"📈 Total results: {len(results)}")

# Sort by date to get the latest first
results_sorted = sorted(results, key=lambda x: x['message']['fulldate'] if x.get('message') and x['message'].get('fulldate') else '1900-01-01', reverse=True)

if results_sorted:
    print("\n" + "="*60)
    print("📋 @UNIOPN CHANNEL RESULTS:")
    print("="*60)
    
    # Show channel info
    if results_sorted:
        channel_info = results_sorted[0]
        print(f"📺 Channel: {channel_info.get('fullName', 'N/A')}")
        print(f"👥 Followers: {channel_info.get('followers', 'N/A'):,}")
        print(f"📝 Bio: {channel_info.get('bio', 'N/A')[:100]}...")
        print()
    
    # Show recent signals/messages
    signal_count = 0
    message_count = 0
    for result in results_sorted:
        if result.get('message') and result['message'].get('description'):
            message_count += 1
            desc = result['message']['description']
            
            # Check if it's a trading signal
            if any(keyword in desc for keyword in ['سیگنال', 'ارز', 'لانگ', 'شورت', 'اهداف', '🚨', 'signal', 'long', 'short']):
                signal_count += 1
                if signal_count <= 3:  # Show top 3 signals
                    msg = result['message']
                    print(f"🔥 Signal {signal_count}:")
                    print(f"   📅 Date: {msg.get('date', 'N/A')} ({msg.get('fulldate', 'N/A')})")
                    print(f"   👀 Views: {msg.get('views', 'N/A')}")
                    print(f"   💬 Signal: {desc[:250]}...")
                    print(f"   🔗 Link: {msg.get('link', 'N/A')}")
                    print("-" * 40)
            elif message_count <= 5:  # Show first 5 messages if not signals
                msg = result['message']
                print(f"📝 Message {message_count}:")
                print(f"   📅 Date: {msg.get('date', 'N/A')} ({msg.get('fulldate', 'N/A')})")
                print(f"   👀 Views: {msg.get('views', 'N/A')}")
                print(f"   💬 Text: {desc[:200]}...")
                print(f"   🔗 Link: {msg.get('link', 'N/A')}")
                print("-" * 40)
    
    print(f"\n📊 Found {signal_count} signals and {message_count} total messages")
    
    # Save results
    with open('/workspace/uniopn_results.json', 'w', encoding='utf-8') as f:
        json.dump(results_sorted, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Results saved to: uniopn_results.json")
else:
    print("❌ No results found for @uniopn")
    print("🔍 This could mean:")
    print("   - Channel is private/restricted")
    print("   - No messages in the last 7 days")
    print("   - Channel name might be different")
    print("   - Channel might be inactive")