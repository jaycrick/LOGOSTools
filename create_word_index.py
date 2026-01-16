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
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format (default: both)",
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

    args = parser.parse_args()

    # Create the index
    word_index = create_word_index(args.json_dir)

    if not word_index:
        print("No words found!")
        return

    # Save in requested format(s)
    if args.format in ["json", "both"]:
        save_index_as_json(word_index, args.json_output)

    if args.format in ["markdown", "both"]:
        save_index_as_markdown(word_index, args.markdown_output)


if __name__ == "__main__":
    main()
