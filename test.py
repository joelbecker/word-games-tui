import argparse
from datetime import datetime


def test_connections():
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

def test_mini():
    from mini import scrape
    date, grid, clues = scrape.get_mini_puzzle()
    print(grid)
    print(clues)
    
if __name__ == "__main__":
    tests = {
        "connections": test_connections,
        "mini": test_mini,
    }

    parser = argparse.ArgumentParser(description="Run test functions.")
    parser.add_argument("--test", choices=tests.keys(), required=True, help="Choose the test to run.")
    args = parser.parse_args()

    # Run the specified test
    
    tests[args.test]()