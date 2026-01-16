#!/usr/bin/env python3
"""
Create a master word index from JSON chapter files.
Produces an alphabetically sorted list of all unique words with their first chapter appearance.
"""

import json
import os
import unicodedata
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


def extract_words_with_sections(json_data):
    """Extract all words from a chapter JSON structure with their sections"""
    words_with_sections = []

    if "sections" in json_data:
        for section in json_data["sections"]:
            section_name = section.get("section", "Unknown")
            if "words" in section:
                for word_entry in section["words"]:
                    book_entry = word_entry.get("book_entry", "").strip()
                    if book_entry:
                        primary_word = book_entry.split("|")[0].strip()
                        words_with_sections.append((primary_word, section_name))

    return words_with_sections


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


def create_sectioned_word_index(json_dir="json"):
    """
    Create a word index organized by grammatical sections.

    Args:
        json_dir: Directory containing JSON chapter files

    Returns:
        A dictionary mapping sections to words to their first chapter number
    """
    section_words = {}

    json_path = Path(json_dir)
    if not json_path.exists():
        print(f"Error: Directory '{json_dir}' not found")
        return section_words

    # Get all JSON files and sort them by chapter number
    json_files = sorted(
        json_path.glob("*.json"), key=lambda f: extract_chapter_number(f.name) or 0
    )

    if not json_files:
        print(f"No JSON files found in '{json_dir}'")
        return section_words

    print(f"Processing {len(json_files)} chapter files for sectioned index...")

    for json_file in json_files:
        chapter_num = extract_chapter_number(json_file.name)

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            words_with_sections = extract_words_with_sections(data)

            for word, section_name in words_with_sections:
                # Initialize section if not exists
                if section_name not in section_words:
                    section_words[section_name] = {}

                # Only add if we haven't seen this word in this section before
                if word not in section_words[section_name]:
                    section_words[section_name][word] = chapter_num

            print(f"  Chapter {chapter_num}: processed")

        except json.JSONDecodeError:
            print(f"  Error: Could not parse {json_file.name}")
        except Exception as e:
            print(f"  Error processing {json_file.name}: {e}")

    return section_words


def save_index_as_json(word_index, output_file="word_index.json"):
    """Save the word index as a JSON file"""
    # Sort alphabetically with custom sort key
    sorted_index = dict(sorted(word_index.items(), key=lambda x: get_sort_key(x[0])))

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(sorted_index, f, ensure_ascii=False, indent=2)

    print(f"\nIndex saved to {output_file}")
    print(f"Total unique words: {len(sorted_index)}")


def save_index_as_markdown(word_index, output_file="word_index.md"):
    """Save the word index as a markdown file"""
    sorted_words = sorted(word_index.items(), key=lambda x: get_sort_key(x[0]))

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Master Word Index\n\n")
        f.write(f"Total unique words: {len(sorted_words)}\n\n")
        f.write("| Word | Chapter |\n")
        f.write("|------|----------|\n")

        for word, chapter in sorted_words:
            f.write(f"| {word} | {chapter} |\n")

    print(f"Index saved to {output_file}")
    print(f"Total unique words: {len(sorted_words)}")


def get_sort_key(word):
    """Generate a sort key that treats uppercase and lowercase as equivalent and strips underscores"""
    # Strip underscores for sorting
    clean_word = word.strip("_")
    # Normalize to NFD (consistent with orig_md_to_json.py) and convert to lowercase for case-insensitive sorting
    normalized = unicodedata.normalize("NFD", clean_word)
    return normalized.lower()


def format_word_for_html(word):
    """Format word for HTML, italicizing if surrounded by underscores"""
    if word.startswith("_") and word.endswith("_"):
        # Remove underscores and wrap in em tags
        clean_word = word[1:-1]
        return f"<em>{clean_word}</em>"
    return word


def save_sectioned_index_as_json(
    section_words, output_file="word_index_by_section.json"
):
    """Save the sectioned word index as a JSON file"""
    # Sort sections and words within sections alphabetically
    sorted_sections = {}
    for section in sorted(section_words.keys()):
        sorted_words = dict(
            sorted(section_words[section].items(), key=lambda x: get_sort_key(x[0]))
        )
        sorted_sections[section] = sorted_words

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(sorted_sections, f, ensure_ascii=False, indent=2)

    total_words = sum(len(words) for words in section_words.values())
    print(f"\nSectioned index saved to {output_file}")
    print(f"Total unique words: {total_words}")
    print(f"Total sections: {len(section_words)}")


def save_sectioned_index_as_markdown(
    section_words, output_file="word_index_by_section.md"
):
    """Save the sectioned word index as a markdown file"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Master Word Index by Section\n\n")
        total_words = sum(len(words) for words in section_words.values())
        f.write(f"Total unique words: {total_words}\n")
        f.write(f"Total sections: {len(section_words)}\n\n")

        for section in sorted(section_words.keys()):
            f.write(f"## {section}\n\n")
            f.write("| Word | Chapter |\n")
            f.write("|------|----------|\n")

            sorted_words = sorted(
                section_words[section].items(), key=lambda x: get_sort_key(x[0])
            )
            for word, chapter in sorted_words:
                f.write(f"| {word} | {chapter} |\n")
            f.write("\n")

    total_words = sum(len(words) for words in section_words.values())
    print(f"\nSectioned index saved to {output_file}")
    print(f"Total unique words: {total_words}")
    print(f"Total sections: {len(section_words)}")


def save_sectioned_index_as_html(
    section_words, output_file="word_index_by_section.html"
):
    """Save the sectioned word index as an HTML file with column-ordered layout"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Master Word Index by Section</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: white;
            line-height: 1.6;
            font-size: 16px;
        }

        h1 {
            font-size: 28px;
            margin: 20px 0 10px 0;
            padding: 0 20px;
        }

        .header-info {
            font-size: 14px;
            color: #666;
            padding: 0 20px 20px 20px;
        }

        .toc {
            padding: 0 20px 20px 20px;
        }

        .toc h2 {
            font-size: 15px;
            margin-bottom: 10px;
            color: #333;
            font-weight: 600;
        }

        .toc-items {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 8px;
        }

        .toc-item {
            padding: 6px 10px;
            background-color: #f5f5f5;
            border-left: 3px solid #333;
            font-size: 14px;
        }

        .toc-item a {
            color: #0066cc;
            text-decoration: none;
        }

        .toc-item a:hover {
            text-decoration: underline;
        }

        .main-content {
            padding: 0 20px;
            margin-bottom: 40px;
        }

        .section-container {
            margin-bottom: 30px;
        }

        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            padding: 10px 0;
            margin: 20px 0 15px 0;
            border-bottom: 1px solid #ccc;
        }

        .section-count {
            color: #999;
            font-size: 13px;
            margin-left: 8px;
            font-weight: normal;
        }

        .word-list {
            padding: 0;
            display: grid;
            grid-auto-flow: column;
            gap: 20px 40px;
        }

        .word-entry {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 15px;
            font-size: 16px;
        }

        .word {
            font-family: 'SBL Greek','SBL BibLit','New Athena Unicode','DejaVu Sans',Athena,Gentium,'Gentium Plus','Palatino Linotype',Menaion,Times,'Arial Unicode MS','Lucida Sans Unicode','Lucida Grande','Code2000',sans-serif;
            font-weight: 500;
            color: #333;
            flex: 1;
            min-width: 0;
        }

        .word em {
            font-style: italic;
            font-weight: 500;
        }

        .chapter {
            color: #999;
            font-size: 13px;
            white-space: nowrap;
            flex-shrink: 0;
        }

        @media print {
            body {
                background-color: white;
            }
            .section-title {
                page-break-after: avoid;
            }
            .section-container {
                page-break-inside: avoid;
            }
        }
    </style>
</head>
<body>
    <h1>Master Word Index by Section</h1>
    <div class="header-info">"""

    total_words = sum(len(words) for words in section_words.values())
    html_content += f"Total unique words: {total_words} | Total sections: {len(section_words)}</div>\n"

    # Table of Contents
    sections_list = sorted(section_words.keys())
    html_content += """    <div class="toc">
        <h2>Sections</h2>
        <div class="toc-items">
"""

    for section in sections_list:
        word_count = len(section_words[section])
        section_id = section.replace(" ", "_").replace(",", "").replace(".", "")
        html_content += f'            <div class="toc-item"><a href="#{section_id}">{section}</a> ({word_count})</div>\n'

    html_content += """        </div>
    </div>

    <div class="main-content">
"""

    for section in sections_list:
        sorted_words = sorted(
            section_words[section].items(), key=lambda x: get_sort_key(x[0])
        )
        section_id = section.replace(" ", "_").replace(",", "").replace(".", "")

        # Calculate number of rows for column-based layout
        # Aim for about 20-30 rows per column for readability
        num_words = len(sorted_words)
        num_rows = max(20, (num_words + 3) // 4)  # Divide by 4 to get ~4 columns max

        html_content += f"""        <div class="section-container">
            <div class="section-title" id="{section_id}">{section} <span class="section-count">({len(sorted_words)})</span></div>
            <div class="word-list" style="grid-template-rows: repeat({num_rows}, auto);">
"""

        for word, chapter in sorted_words:
            formatted_word = format_word_for_html(word)
            html_content += f'                <div class="word-entry"><span class="word">{formatted_word}</span><span class="chapter">Ch. {chapter}</span></div>\n'

        html_content += """            </div>
        </div>
"""

    html_content += """    </div>
</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\nSectioned index saved to {output_file}")
    print(f"Total unique words: {total_words}")
    print(f"Total sections: {len(section_words)}")


def save_index_as_html(word_index, output_file="word_index.html", entries_per_page=102):
    """Save the word index as an HTML file optimized for printing in 3 columns with page breaks"""
    sorted_words = sorted(word_index.items(), key=lambda x: get_sort_key(x[0]))

    # Calculate entries per column (divide page entries by 3 columns)
    entries_per_column = entries_per_page // 3

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Master Word Index</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
        }}

        .page {{
            background-color: white;
            padding: 0.5in;
            page-break-after: always;
        }}

        .page:last-child {{
            page-break-after: auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #333;
        }}

        h1 {{
            font-size: 24px;
            margin-bottom: 5px;
        }}

        .word-count {{
            color: #666;
            font-size: 14px;
        }}

        .columns {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.4in;
            column-rule: 1px solid #ddd;
        }}

        .column {{
            min-width: 0;
        }}

        .word-entry {{
            margin: 4px 0;
            page-break-inside: avoid;
            break-inside: avoid;
            line-height: 1.4;
        }}

        .word {{
            font-family: 'SBL Greek','SBL BibLit','New Athena Unicode','DejaVu Sans',Athena,Gentium,'Gentium Plus','Palatino Linotype',Menaion,Times,'Arial Unicode MS','Lucida Sans Unicode','Lucida Grande','Code2000',sans-serif;
            font-weight: 500;
            color: #000;
        }}

        .word em {{
            font-style: italic;
            font-weight: 500;
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
            .page {{
                margin: 0;
                padding: 0.5in;
                min-height: 0;
            }}
        }}

        @media screen {{
            .page {{
                max-width: 8.5in;
                margin: 20px auto;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
        }}
    </style>
</head>
<body>
"""

    # Split words into pages
    page_num = 0
    i = 0
    total_words = len(sorted_words)

    while i < total_words:
        page_num += 1
        page_words = sorted_words[i : i + entries_per_page]

        # Add page header only on first page
        if page_num == 1:
            html_content += f"""    <div class="page">
        <div class="header">
            <h1>Master Word Index</h1>
            <div class="word-count">Total unique words: {total_words}</div>
        </div>
        <div class="columns">
"""
        else:
            html_content += """    <div class="page">
        <div class="columns">
"""

        # Distribute words into 3 columns
        words_per_column = len(page_words) // 3
        remainder = len(page_words) % 3

        col_start = 0
        for col_num in range(3):
            # Distribute remainder across first columns
            col_size = words_per_column + (1 if col_num < remainder else 0)
            col_words = page_words[col_start : col_start + col_size]

            html_content += '            <div class="column">\n'
            for word, chapter in col_words:
                formatted_word = format_word_for_html(word)
                html_content += f'                <div class="word-entry"><span class="word">{formatted_word}</span><span class="chapter">Ch. {chapter}</span></div>\n'
            html_content += "            </div>\n"

            col_start += col_size

        html_content += """        </div>
    </div>
"""

        i += entries_per_page

    html_content += """</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Index saved to {output_file}")
    print(f"Total unique words: {len(sorted_words)}")
    print(f"Distributed across {page_num} pages ({entries_per_page} entries per page)")


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
    parser.add_argument(
        "--entries-per-page",
        type=int,
        default=102,
        help="Number of entries per page for HTML output (default: 102)",
    )
    parser.add_argument(
        "--include-sectioned",
        action="store_true",
        help="Also generate sectioned index (organized by grammatical sections)",
    )
    parser.add_argument(
        "--sectioned-only",
        action="store_true",
        help="Generate only the sectioned index",
    )
    parser.add_argument(
        "--section-json-output",
        default="word_index_by_section.json",
        help="Output JSON filename for sectioned index (default: word_index_by_section.json)",
    )
    parser.add_argument(
        "--section-markdown-output",
        default="word_index_by_section.md",
        help="Output markdown filename for sectioned index (default: word_index_by_section.md)",
    )
    parser.add_argument(
        "--section-html-output",
        default="word_index_by_section.html",
        help="Output HTML filename for sectioned index (default: word_index_by_section.html)",
    )

    args = parser.parse_args()

    # Create regular index unless only sectioned is requested
    if not args.sectioned_only:
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
            save_index_as_html(word_index, args.html_output, args.entries_per_page)

    # Create sectioned index if requested
    if args.include_sectioned or args.sectioned_only:
        section_words = create_sectioned_word_index(args.json_dir)

        if not section_words:
            print("No words found for sectioned index!")
            return

        # Save in requested format(s)
        if args.format in ["json", "all"]:
            save_sectioned_index_as_json(section_words, args.section_json_output)

        if args.format in ["markdown", "all"]:
            save_sectioned_index_as_markdown(
                section_words, args.section_markdown_output
            )

        if args.format in ["html", "all"]:
            save_sectioned_index_as_html(section_words, args.section_html_output)


if __name__ == "__main__":
    main()
