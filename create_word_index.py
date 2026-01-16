#!/usr/bin/env python3
"""
Create a master word index from JSON chapter files.
Produces an alphabetically sorted list of all unique words with their first chapter appearance.
"""

import json
import os
from collections import defaultdict
from pathlib import Path


def extract_chapter_number(filename):
    """Extract chapter number from filename (e.g., 'Ch 1.json' -> 1)"""
    name = Path(filename).stem  # Remove .json extension
    parts = name.split()
    if parts[0].lower() == "ch" and len(parts) > 1:
        try:
            return int(parts[1])
        except ValueError:
            return None
    return None


def extract_words_from_chapter(json_data):
    """Extract all words from a chapter JSON structure"""
    words = []

    if "sections" in json_data:
        for section in json_data["sections"]:
            if "words" in section:
                for word_entry in section["words"]:
                    # Extract the word form (before comma if present)
                    book_entry = word_entry.get("book_entry", "").strip()
                    if book_entry:
                        # Get just the first word form if there are alternatives
                        primary_word = book_entry.split("|")[0].strip()
                        words.append(primary_word)

    return words


def create_word_index(json_dir="json"):
    """
    Create a master word index from all JSON chapter files.

    Args:
        json_dir: Directory containing JSON chapter files

    Returns:
        A dictionary mapping words to their first chapter number
    """
    word_to_chapter = {}

    json_path = Path(json_dir)
    if not json_path.exists():
        print(f"Error: Directory '{json_dir}' not found")
        return word_to_chapter

    # Get all JSON files and sort them by chapter number
    json_files = sorted(
        json_path.glob("*.json"), key=lambda f: extract_chapter_number(f.name) or 0
    )

    if not json_files:
        print(f"No JSON files found in '{json_dir}'")
        return word_to_chapter

    print(f"Processing {len(json_files)} chapter files...")

    for json_file in json_files:
        chapter_num = extract_chapter_number(json_file.name)

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            words = extract_words_from_chapter(data)

            for word in words:
                # Only add if we haven't seen this word before (first occurrence)
                if word not in word_to_chapter:
                    word_to_chapter[word] = chapter_num

            print(f"  Chapter {chapter_num}: {len(words)} words extracted")

        except json.JSONDecodeError:
            print(f"  Error: Could not parse {json_file.name}")
        except Exception as e:
            print(f"  Error processing {json_file.name}: {e}")

    return word_to_chapter


def save_index_as_json(word_index, output_file="word_index.json"):
    """Save the word index as a JSON file"""
    # Sort alphabetically
    sorted_index = dict(sorted(word_index.items()))

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(sorted_index, f, ensure_ascii=False, indent=2)

    print(f"\nIndex saved to {output_file}")
    print(f"Total unique words: {len(sorted_index)}")


def save_index_as_markdown(word_index, output_file="word_index.md"):
    """Save the word index as a markdown file"""
    sorted_words = sorted(word_index.items())

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Master Word Index\n\n")
        f.write(f"Total unique words: {len(sorted_words)}\n\n")
        f.write("| Word | Chapter |\n")
        f.write("|------|----------|\n")

        for word, chapter in sorted_words:
            f.write(f"| {word} | {chapter} |\n")

    print(f"Index saved to {output_file}")
    print(f"Total unique words: {len(sorted_words)}")


def save_index_as_html(word_index, output_file="word_index.html"):
    """Save the word index as an HTML file optimized for printing in 3 columns"""
    sorted_words = sorted(word_index.items())

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Master Word Index</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0.5in;
            line-height: 1.4;
            background-color: #f5f5f5;
        }}
        
        .container {{
            background-color: white;
            padding: 0.5in;
            column-count: 3;
            column-gap: 0.4in;
            column-rule: 1px solid #ddd;
        }}
        
        h1 {{
            column-span: all;
            text-align: center;
            margin-top: 0;
            font-size: 24px;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }}
        
        .word-count {{
            column-span: all;
            text-align: center;
            color: #666;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        
        .word-entry {{
            margin: 4px 0;
            page-break-inside: avoid;
            break-inside: avoid;
        }}
        
        .word {{
            font-weight: 500;
            color: #000;
        }}
        
        .chapter {{
            color: #666;
            font-size: 0.9em;
            margin-left: 1em;
        }}
        
        @media print {{
            body {{
                margin: 0;
                background-color: white;
            }}
            .container {{
                margin: 0;
                padding: 0.5in;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Master Word Index</h1>
        <div class="word-count">Total unique words: {len(sorted_words)}</div>
"""

    for word, chapter in sorted_words:
        html_content += f'        <div class="word-entry"><span class="word">{word}</span><span class="chapter">Ch. {chapter}</span></div>\n'

    html_content += """    </div>
</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Index saved to {output_file}")
    print(f"Total unique words: {len(sorted_words)}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Create a master word index from Greek text chapters"
    )
    parser.add_argument(
        "--json-dir",
        default="json",
        help="Directory containing JSON chapter files (default: json)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "html", "all"],
        default="all",
        help="Output format: json, markdown, html, or all (default: all)",
    )
    parser.add_argument(
        "--json-output",
        default="word_index.json",
        help="Output JSON filename (default: word_index.json)",
    )
    parser.add_argument(
        "--markdown-output",
        default="word_index.md",
        help="Output markdown filename (default: word_index.md)",
    )
    parser.add_argument(
        "--html-output",
        default="word_index.html",
        help="Output HTML filename (default: word_index.html)",
    )

    args = parser.parse_args()

    # Create the index
    word_index = create_word_index(args.json_dir)

    if not word_index:
        print("No words found!")
        return

    # Save in requested format(s)
    if args.format in ["json", "all"]:
        save_index_as_json(word_index, args.json_output)

    if args.format in ["markdown", "all"]:
        save_index_as_markdown(word_index, args.markdown_output)

    if args.format in ["html", "all"]:
        save_index_as_html(word_index, args.html_output)


if __name__ == "__main__":
    main()
