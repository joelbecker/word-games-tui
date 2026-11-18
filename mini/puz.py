"""Read Across Lite .puz files and convert them to ipuz.

Format reference: https://code.google.com/archive/p/puz/wikis/FileFormat.wiki
Supports circled cells (GEXT) and rebus cells (GRBS/RTBL). Scrambled
(locked) puzzles are rejected because their solution can't be read.
"""
import struct

MAGIC = b"ACROSS&DOWN\0"
HEADER_SIZE = 0x34
BLACK = "."
CIRCLED = 0x80


def _decode(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("iso-8859-1")


def _read_strings(data: bytes, offset: int, count: int):
    strings = []
    for _ in range(count):
        end = data.index(b"\0", offset)
        strings.append(_decode(data[offset:end]))
        offset = end + 1
    return strings, offset


def _read_sections(data: bytes, offset: int) -> dict:
    """Extra sections: 4-byte name, 2-byte length, 2-byte checksum, data, NUL."""
    sections = {}
    while offset + 8 <= len(data):
        name = data[offset:offset + 4].decode("ascii", "replace")
        (length,) = struct.unpack_from("<H", data, offset + 4)
        sections[name] = data[offset + 8:offset + 8 + length]
        offset += 8 + length + 1
    return sections


def parse_puz(data: bytes) -> dict:
    start = data.find(MAGIC)
    if start < 2:
        raise ValueError("Not a .puz file")
    data = data[start - 2:]
    width, height, num_clues, _puzzle_type, scrambled = struct.unpack_from("<BBHHH", data, 0x2C)
    if scrambled:
        raise ValueError("Scrambled .puz files are not supported")

    size = width * height
    solution = _decode(data[HEADER_SIZE:HEADER_SIZE + size])
    offset = HEADER_SIZE + 2 * size  # Skip the player's fill grid
    (title, author, copyright_), offset = _read_strings(data, offset, 3)
    clues, offset = _read_strings(data, offset, num_clues)
    sections = _read_sections(data, data.index(b"\0", offset) + 1)  # Skip notes

    rebus = {}
    if "GRBS" in sections and "RTBL" in sections:
        table = {}
        for entry in _decode(sections["RTBL"]).split(";"):
            if ":" in entry:
                key, value = entry.split(":", 1)
                table[int(key.strip())] = value
        for index, value in enumerate(sections["GRBS"]):
            if value:
                rebus[index] = table.get(value - 1)

    return {
        "width": width,
        "height": height,
        "solution": solution,
        "title": title,
        "author": author,
        "copyright": copyright_,
        "clues": clues,
        "circled": {i for i, flags in enumerate(sections.get("GEXT", b"")) if flags & CIRCLED},
        "rebus": rebus,
    }


def puz_to_ipuz(data: bytes) -> dict:
    p = parse_puz(data)
    width, height, solution = p["width"], p["height"], p["solution"]

    def is_black(row, col):
        return row < 0 or col < 0 or row >= height or col >= width or solution[row * width + col] == BLACK

    puzzle, solution_grid = [], []
    clues = {"Across": [], "Down": []}
    remaining_clues = iter(p["clues"])
    number = 0
    for row in range(height):
        puzzle_row, solution_row = [], []
        for col in range(width):
            index = row * width + col
            if is_black(row, col):
                puzzle_row.append("#")
                solution_row.append("#")
                continue
            # Clues are stored in numbering order, across before down for each number
            starts_across = is_black(row, col - 1) and not is_black(row, col + 1)
            starts_down = is_black(row - 1, col) and not is_black(row + 1, col)
            label = 0
            if starts_across or starts_down:
                number += 1
                label = number
                if starts_across:
                    clues["Across"].append([number, next(remaining_clues)])
                if starts_down:
                    clues["Down"].append([number, next(remaining_clues)])
            if index in p["circled"]:
                puzzle_row.append({"cell": label, "style": {"shapebg": "circle"}})
            else:
                puzzle_row.append(label)
            solution_row.append(p["rebus"].get(index) or solution[index])
        puzzle.append(puzzle_row)
        solution_grid.append(solution_row)

    if next(remaining_clues, None) is not None:
        raise ValueError("More clues than numbered squares")

    return {
        "version": "http://ipuz.org/v2",
        "kind": ["http://ipuz.org/crossword#1"],
        "title": p["title"],
        "author": p["author"],
        "copyright": p["copyright"],
        "dimensions": {"width": width, "height": height},
        "puzzle": puzzle,
        "solution": solution_grid,
        "clues": clues,
    }
