import os
import json
import time
from utils import scrape_with_selenium

MINI_PUZZLE_FILENAME = os.path.expanduser("~/.wordgames/mini.json")

def reveal_mini_solution(driver):
    continue_button = driver.find_element("xpath", '/html/body/div[5]/div/div/button')
    continue_button.click()
    time.sleep(1)

    overlay = driver.find_element("xpath", '//*[@id="portal-game-modals"]/div/div/div[2]/article/button')
    overlay.click()
    time.sleep(1) 
    
    reveal_button = driver.find_element("xpath", '//*[@id="portal-game-toolbar"]/div/ul/div[2]/li[2]/button')
    reveal_button.click()
    time.sleep(1)
    
    puzzle_button = driver.find_element("xpath", '//*[@id="portal-game-toolbar"]/div/ul/div[2]/li[2]/ul/li[3]/button')
    puzzle_button.click()
    time.sleep(1)

    confirm_button = driver.find_element("xpath", '//*[@id="portal-game-modals"]/div/div/div[2]/article/div/button[2]')
    confirm_button.click()


def get_mini_puzzle():
    import bs4

    url = "https://www.nytimes.com/crosswords/game/mini"

    use_cached = True

    if use_cached:
        # temporary to avoid rate limiting
        with open("mini.html", "r") as f:
            # f.write(html)
            html = f.read()
    else:
        html = scrape_with_selenium(
            url,
            driver_actions=reveal_mini_solution,
        )
        with open("mini.html", "w") as f:
            f.write(html)

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