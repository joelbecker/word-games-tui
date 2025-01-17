from datetime import datetime

from connections import scrape

dates = [
    datetime(2024, 12, 6),
    datetime(2024, 12, 7),
    datetime(2024, 12, 8),
    datetime(2024, 12, 9),
    datetime(2024, 12, 10),
    datetime(2024, 12, 11),
    datetime(2025, 1, 1),
    datetime(2025, 1, 2),
    datetime(2025, 1, 6),
    datetime.today(),
]

for date in dates:
    print(f"Fetching {date}")
    scrape.fetch_latest_connections_puzzle(date)

print("Done")
