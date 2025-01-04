from termcolor import colored

grid=r"""     ___     
 ___/ A \___ 
/ X \___/ B \
\___/ C \___/
/ Y \___/ Z \
\___/ D \___/
    \___/    
"""

color_mapping = [
    (33, 36, "yellow"),
    (46, 51, "yellow"),
    (60, 65, "yellow"),
    (14+6, 14+7, "white"),
    (14*2+2, 14*2+3, "white"),
    (14*2+10, 14*2+11, "white"),
    (14*4+2, 14*4+3, "white"),
    (14*4+10, 14*4+11, "white"),
    (14*5+6, 14*5+7, "white"),
]

colored_grid = ""

for i in range(len(grid)):
    chr_color = "grey"
    for start, end, span_color in color_mapping:
        if i >= start and i < end:
            chr_color = span_color
            break
    colored_grid += colored(grid[i], chr_color)

print(colored_grid)