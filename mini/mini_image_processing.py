import os
import cv2
import numpy as np
import pytesseract

def extract_crossword_puzzle(image_path):
    # Read the image
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(os.path.expanduser('~/Downloads/gray_crossword.png'), gray)    

    # Threshold the image
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    cv2.imwrite(os.path.expanduser('~/Downloads/thresh_crossword.png'), thresh)    

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    # Sort contours by area to find cells
    cell_contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    # Initialize 7x7 grid
    puzzle = [['#' for _ in range(7)] for _ in range(7)]
    contour_strs = []
    # For each cell contour
    for contour in cell_contours:
        x, y, w, h = cv2.boundingRect(contour)
        # Extract the cell
        cell = gray[y:y+h, x:x+w]
        
        # Use OCR to recognize the letter
        letter = pytesseract.image_to_string(cell, config='--psm 10')
        contour_strs.append(letter)
        # Calculate grid position
        grid_x = x // (img.shape[1] // 7)
        grid_y = y // (img.shape[0] // 7)
        
        if grid_x < 7 and grid_y < 7:
            # Clean the OCR result
            letter = letter.strip()
            if letter.isalpha() and len(letter) == 1:
                puzzle[grid_y][grid_x] = letter

    return puzzle, contour_strs

def print_puzzle(puzzle):
    for row in puzzle:
        print(' '.join(row))

# Usage
puzzle, contour_strs = extract_crossword_puzzle('/Users/joelweberbecker/Downloads/completed-nyt-mini-crossword-puzzle-for-jan-4-2025.webp')
print_puzzle(puzzle)
print(contour_strs)