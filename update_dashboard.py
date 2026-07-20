import shutil
import os

SOURCE = os.path.expanduser("~/signals")
DESTINATION = os.path.expanduser("~/godo-ai/assets/data")

FILES = [
    "engine_status.json",
    "signal_statistics.json",
    "trade_statistics.json",
    "active_signals.json",
    "active_trades.json",
    "latest_signals.json",
    "latest_prices.json"
]

for file in FILES:
    source_file = os.path.join(SOURCE, file)
    destination_file = os.path.join(DESTINATION, file)

    if os.path.exists(source_file):
        shutil.copy2(source_file, destination_file)
        print(f"✅ Copied: {file}")
    else:
        print(f"❌ Missing: {file}")

print("\n🚀 Dashboard Data Updated Successfully!")
