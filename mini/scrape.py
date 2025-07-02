import os
import json
import time
import inspect
from utils import full_page_screenshot, scrape_with_selenium

MINI_PUZZLE_FILENAME = os.path.expanduser("~/.wordgames/mini.json")
SCREENSHOT_DIR = os.path.expanduser("~/Downloads/")

def _is_called_from_test():
    """Check if the current function is being called from test.py"""
    for frame_info in inspect.stack():
        if frame_info.filename.endswith('test.py'):
            return True
    return False

def reveal_mini_solution(driver):
    # Only save screenshots if called from test.py
    save_screenshots = _is_called_from_test()
    
    if save_screenshots:
        full_page_screenshot(driver, os.path.join(SCREENSHOT_DIR, "__1_mini_full_page.png"))
    continue_button = driver.find_element("xpath", '//*[@id="portal-game-modals"]/div/div/div[2]/article/button')
    continue_button.click()
    time.sleep(1)
    
    if save_screenshots:
        full_page_screenshot(driver, os.path.join(SCREENSHOT_DIR, "__2_mini_reveal_button.png"))
    reveal_button = driver.find_element("xpath", '//*[@id="portal-game-toolbar"]/div/ul/div[2]/li[2]/button')
    reveal_button.click()
    time.sleep(1)
    
    if save_screenshots:
        full_page_screenshot(driver, os.path.join(SCREENSHOT_DIR, "__3_mini_puzzle_button.png"))
    puzzle_button = driver.find_element("xpath", '//*[@id="portal-game-toolbar"]/div/ul/div[2]/li[2]/ul/li[3]/button')
    puzzle_button.click()
    time.sleep(1)

    if save_screenshots:
        full_page_screenshot(driver, os.path.join(SCREENSHOT_DIR, "__4_mini_confirm_button.png"))
    confirm_button = driver.find_element("xpath", '//*[@id="portal-game-modals"]/div/div/div[2]/article/div/button[2]')
    confirm_button.click()


def get_mini_puzzle():
    import bs4

    url = "https://www.nytimes.com/crosswords/game/mini"

    use_cached = False

    html = scrape_with_selenium(
        url,
        driver_actions=reveal_mini_solution,
    )

    soup = bs4.BeautifulSoup(html, "html.parser")

    raw_date = soup.find("div", attrs={"class": "xwd__details--date"}).contents[0].strip().split(", ")[1]
    current_year = time.strftime("%Y")
    raw_date_with_year = f"{raw_date}, {current_year}"
    date = time.strftime("%Y-%m-%d", time.strptime(raw_date_with_year, "%B %d, %Y"))
    
    g_elements = soup.find_all("g", attrs={"class": "xwd__cell"})

    def parse_cell(g):
        texts = g.find_all("text", attrs={"data-testid": "cell-text"})
        number = texts[0].text if len(texts) > 1 else ""
        letter = texts[-1].text.strip()[0] if texts else ""
        
        return {
            "class": g.rect.get("class"),
            "x": float(g.rect.get("x")),
            "y": float(g.rect.get("y")),
            "number": number,
            "letter": letter,
            "has_circle": bool(g.circle) or (g.path and g.path.attrs['data-testid'] == "cell-path") or False,
        }

    cells = [parse_cell(g) for g in g_elements]

    cols = sorted(list(set(c["x"] for c in cells)))
    rows = sorted(list(set(c["y"] for c in cells)))
    grid = [[None for _ in cols] for _ in rows]

    for cell in cells:
        row = rows.index(cell["y"])
        col = cols.index(cell["x"])

        if "xwd__cell--block" in cell["class"]:
            grid[row][col] = {
                "solution": None,
                "number": None,
                "is_circled": False,
                "i": row,
                "j": col,
                "is_out_of_bounds": True,
            }
        else:
            grid[row][col] = {
                "solution": cell["letter"],
                "number": cell["number"],
                "is_circled": cell["has_circle"],
                "i": row,
                "j": col,
            }

    clue_lists = soup.find_all("div", attrs={"class": "xwd__clue-list--wrapper"})
    clues = soup.find_all("li", attrs={"class": "xwd__clue--li"})
    clues = []

    for clue_list in clue_lists:
        direction = clue_list.find("h3").text
        for li in clue_list.find_all("li", attrs={"class": "xwd__clue--li"}):
            clue = {
                "number": li.find("span", attrs={"class": "xwd__clue--label"}).text,
                "clue": li.find("span", attrs={"class": "xwd__clue--text"}).text,
                "direction": direction,
            }
            clues.append(clue)

    return date, grid, clues

def write_mini_puzzle_data():
    date, grid, clues = get_mini_puzzle()
    json_data = {
        "date": date,
        "grid": grid,
        "clues": clues,
    }
    with open(MINI_PUZZLE_FILENAME, "w") as f:
        json.dump(json_data, f, indent=4)

