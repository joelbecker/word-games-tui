import bs4


from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def scrape_with_selenium(url):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    html = driver.page_source
    driver.quit()
    return html


def get_mini_puzzle():

    url = "https://www.nytimes.com/crosswords/game/mini"
    # html = scrape_with_selenium(url)

    # temporary to avoid rate limiting
    with open("mini.html", "r") as f:
        html = f.read()

    soup = bs4.BeautifulSoup(html, "html.parser")

    g_elements = soup.find_all("g", attrs={"class": "xwd__cell"})

    def parse_cell(g):
        return {
            "class": g.rect.get("class"),
            "x": float(g.rect.get("x")),
            "y": float(g.rect.get("y")),
            "number": g.text,
        }

    cells = [parse_cell(g) for g in g_elements]

    rows = sorted(list(set(c["x"] for c in cells)))
    cols = sorted(list(set(c["y"] for c in cells)))
    grid = [[None for _ in cols] for _ in rows]

    for cell in cells:
        row = rows.index(cell["y"])
        col = cols.index(cell["x"])
        if "xwd__cell--block" in cell["class"]:
            grid[row][col] = None
        else:
            grid[row][col] = cell["number"]

    clue_lists = soup.find_all("div", attrs={"class": "xwd__clue-list--wrapper"})
    clues = soup.find_all("li", attrs={"class": "xwd__clue--li"})
    clues = []

    for clue_list in clue_lists:
        direction = clue_list.find("h3").text
        for li in clue_list.find_all("li", attrs={"class": "xwd__clue--li"}):
            clue = {
                "number": li.find("span", attrs={"class": "xwd__clue--label"}).text,
                "text": li.find("span", attrs={"class": "xwd__clue--text"}).text,
                "direction": direction,
            }
            clues.append(clue)

    return grid, clues

grid, clues = get_mini_puzzle()
print(grid)
print(clues)
