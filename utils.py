#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Filename:    utils.py
# @Author:      Kuro
# @Time:        3/22/2025 7:27 PM
import json
import re

import fitz
from tqdm import tqdm


def load_tables():
    """Loads extracted tables from JSON file."""
    try:
        with open("tables.json", "r", encoding="utf-8") as f:
            tables = json.load(f)
        return tables
    except FileNotFoundError:
        return []


# Function to clean text
def clean_text(text):
    """Removes extra spaces, newlines, and unwanted characters"""
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"https?://\S+", "", text)  # Remove URLs
    return text


def clean_extracted_text(text):
    """Cleans extracted text by removing excessive spaces, new lines, and formatting issues."""
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces/newlines with a single space
    text = text.strip()  # Remove leading/trailing spaces
    return text


def extract_tables_from_pdf(pdf_path, difference_between_each_row=100):
    """
    Extracts tables from a PDF and groups rows belonging to the same table using bbox.
    Two rows are considered part of the same table if:
      - Their x1 coordinates are equal, and
      - Their y1 coordinates differ by 10 or less.

    Returns a list of text chunks, each representing one full table.
    """
    doc = fitz.open(pdf_path)
    extracted_tables = []

    for page_num, page in enumerate(doc):
        tables = page.find_tables()
        # Variables to hold the current grouped table's text and its bbox.
        current_table_text = ""
        current_bbox = None  # Expected to be a tuple (x0, y0, x1, y1)

        for table in tables:
            # Get the bounding box for the current detected table (row)
            table_bbox = table.bbox

            # Extract table row data as text
            table_data = table.extract()
            table_text = ""
            for row in table_data:
                row_text = ""
                for cell in row:
                    if cell is None or cell == "":
                        continue
                    cell_text = str(cell).strip().replace("\n", "")
                    if cell_text:
                        row_text += cell_text + " | "
                if row_text:
                    # Remove trailing separator and add a newline
                    row_text = row_text.rstrip(" | ") + "\n"
                table_text += row_text

            if current_bbox is None:
                # Start a new group for the first table (row)
                current_table_text = table_text
                current_bbox = table_bbox
            else:
                # Check if current table row belongs to the same table group.
                # Here we compare x1 coordinates for equality and ensure the difference
                # in y1 is at most 10 units.
                if (current_bbox[0] == table_bbox[0] and (abs(current_bbox[1] - table_bbox[1]) <= difference_between_each_row or abs(current_bbox[3] - table_bbox[3]) <= difference_between_each_row)):
                    # Same table, so concatenate the text.
                    current_table_text += table_text
                    # Optionally, update the bbox for the group:
                    current_bbox = (current_bbox[0], current_bbox[1], current_bbox[2], table_bbox[3])
                else:
                    # New table group detected: store the previous group's text.
                    extracted_tables.append(current_table_text)
                    current_table_text = table_text
                    current_bbox = table_bbox

        # Append any remaining grouped table text from the page.
        if current_table_text:
            extracted_tables.append(current_table_text)

    return extracted_tables


def extract_text_from_pdf(pdf_path):
    """Extract text from a two-column PDF in correct reading order, excluding tables."""
    doc = fitz.open(pdf_path)
    extracted_text = []

    for page in tqdm(doc, desc="Extracting ordered text", unit="page"):
        # First identify all tables on the page
        tables = page.find_tables()
        table_rects = [table.bbox for table in tables]

        # Get and sort text blocks
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (round(b[1], 1), round(b[0], 1)))

        for b in blocks:
            if len(b) >= 5:
                # Create a rect object for this text block
                block_rect = fitz.Rect(b[0], b[1], b[2], b[3])

                # Skip if block intersects with any table
                if any(block_rect.intersects(table_rect) for table_rect in table_rects):
                    continue

                text = b[4].strip()
                if re.search(r"Downloaded from|ESC Guidelines|\.\.|©|http|^Table\s", text):
                    continue

                if len(text) < 20:
                    continue

                extracted_text.append(text)

    return "\n".join(extracted_text)


def extract_assistant_response_phi4(response):
    # Regular expression pattern to extract the assistant's reply
    pattern = r'<\|im_start\|>\s*assistant\s*<\|im_sep\|>\s*(.*?)\s*<\|im_end\|>'

    # Search for the pattern in the conversation
    match = re.search(pattern, response, re.DOTALL)

    if match:
        response = match.group(1).strip()
    return response
