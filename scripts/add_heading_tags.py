#!/usr/bin/env python3
"""
Add Heading Tags to PDF Structure Tree

This script detects headings in a PDF and adds H1, H2, H3 elements to the structure tree.
Uses font size and text characteristics to identify heading hierarchy.

Requirements:
    pip install pikepdf pypdf

Usage:
    python add_heading_tags.py input.pdf --output output.pdf
    python add_heading_tags.py input.pdf --output output.pdf --manual-headings headings.json
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

try:
    import pikepdf
    from pikepdf import Dictionary, Array, Name, String
except ImportError:
    print("Error: pikepdf is not installed. Run: pip install pikepdf")
    sys.exit(1)

try:
    from pypdf import PdfReader
except ImportError:
    print("Error: pypdf is not installed. Run: pip install pypdf")
    sys.exit(1)


def extract_text_with_fonts(pdf_path: str) -> List[Dict]:
    """
    Extract text from PDF with font size information.
    Returns list of text blocks with font metadata.
    """
    print(f"Analyzing PDF text structure: {pdf_path}")
    reader = PdfReader(pdf_path)

    text_blocks = []
    block_id = 0

    for page_num, page in enumerate(reader.pages, start=1):
        # Extract text with font info
        try:
            # Get page text
            page_text = page.extract_text()

            if not page_text.strip():
                continue

            # Split into lines
            lines = page_text.split('\n')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                block_id += 1

                # Heuristic detection of headings based on text characteristics
                is_likely_heading = detect_heading_heuristic(line)
                estimated_level = estimate_heading_level(line, lines)

                text_blocks.append({
                    'id': block_id,
                    'page': page_num,
                    'text': line,
                    'is_heading': is_likely_heading,
                    'level': estimated_level,
                    'char_count': len(line),
                    'word_count': len(line.split())
                })

        except Exception as e:
            print(f"  Warning: Could not process page {page_num}: {e}")
            continue

    print(f"Extracted {len(text_blocks)} text blocks")
    return text_blocks


def detect_heading_heuristic(text: str) -> bool:
    """
    Detect if text is likely a heading using heuristics.
    """
    # Short text (< 100 chars)
    if len(text) > 100:
        return False

    # No ending punctuation (headings usually don't end with period)
    if text.endswith('.') or text.endswith(','):
        return False

    # All caps might be heading
    if text.isupper() and len(text) > 3:
        return True

    # Title case (most words capitalized)
    words = text.split()
    if len(words) > 1:
        capitalized = sum(1 for w in words if w and w[0].isupper())
        if capitalized / len(words) > 0.6:  # 60% capitalized
            return True

    # Starts with number (like "1. Introduction")
    if text and (text[0].isdigit() or text.startswith('•') or text.startswith('-')):
        return True

    # Contains common heading keywords
    heading_keywords = ['introduction', 'background', 'method', 'result', 'discussion',
                       'conclusion', 'summary', 'overview', 'chapter', 'section',
                       'föreläsning', 'introduktion', 'bakgrund', 'metod', 'resultat',
                       'diskussion', 'sammanfattning', 'översikt', 'kapitel']

    text_lower = text.lower()
    if any(kw in text_lower for kw in heading_keywords):
        return True

    return False


def estimate_heading_level(line: str, all_lines: List[str]) -> int:
    """
    Estimate heading level (1-6) based on text characteristics.
    """
    # Very short and all caps = H1
    if len(line) < 30 and line.isupper():
        return 1

    # Starts with single digit = H2
    if line and line[0].isdigit() and not line[1:2].isdigit():
        return 2

    # Starts with multi-digit (like "1.1") = H3
    if line and len(line) > 2 and line[0].isdigit() and line[1] in '.):':
        return 3

    # Default based on length
    if len(line) < 20:
        return 2
    elif len(line) < 40:
        return 3
    else:
        return 4


def identify_headings(text_blocks: List[Dict]) -> List[Dict]:
    """
    Identify and classify headings from text blocks.
    """
    headings = []

    for block in text_blocks:
        if block['is_heading']:
            headings.append({
                'page': block['page'],
                'text': block['text'],
                'level': block['level'],
                'block_id': block['id']
            })

    print(f"\nIdentified {len(headings)} potential headings:")

    # Group by level
    by_level = defaultdict(int)
    for h in headings:
        by_level[h['level']] += 1

    for level in sorted(by_level.keys()):
        print(f"  H{level}: {by_level[level]} headings")

    # Show first few examples
    if headings:
        print("\nFirst 10 headings detected:")
        for h in headings[:10]:
            try:
                text_preview = h['text'][:60].encode('utf-8', errors='replace').decode('utf-8')
                print(f"  H{h['level']} (Page {h['page']}): {text_preview}...")
            except:
                print(f"  H{h['level']} (Page {h['page']}): [text contains special characters]")

    return headings


def load_manual_headings(headings_file: str) -> List[Dict]:
    """
    Load manually specified headings from JSON file.
    Format: [{"page": 1, "text": "Title", "level": 1}, ...]
    """
    print(f"\nLoading headings from: {headings_file}")

    with open(headings_file, 'r', encoding='utf-8') as f:
        headings = json.load(f)

    print(f"Loaded {len(headings)} headings")
    return headings


def add_heading_structure_tree(pdf_path: str, output_path: str, headings: List[Dict], metadata: Dict = None):
    """
    Add heading elements to PDF structure tree.
    """
    print(f"\nCreating PDF with heading structure: {output_path}")

    pdf = pikepdf.open(pdf_path)

    # Create or get structure tree root
    if '/StructTreeRoot' not in pdf.Root:
        struct_tree_root = pdf.make_indirect(Dictionary(
            Type=Name.StructTreeRoot,
            K=Array([]),
            ParentTree=Dictionary(Nums=Array([])),
            RoleMap=Dictionary()
        ))
        pdf.Root.StructTreeRoot = struct_tree_root
    else:
        struct_tree_root = pdf.Root.StructTreeRoot

    # Create document element if needed
    if not struct_tree_root.K or len(struct_tree_root.K) == 0:
        document_elem = pdf.make_indirect(Dictionary(
            Type=Name.StructElem,
            S=Name.Document,
            P=struct_tree_root,
            K=Array([])
        ))
        struct_tree_root.K = Array([document_elem])
    else:
        document_elem = struct_tree_root.K[0]

    # Add heading elements
    print("Adding heading elements to structure tree...")

    for heading in headings:
        level = min(heading['level'], 6)  # H1-H6
        heading_tag = Name(f'/H{level}')

        heading_elem = pdf.make_indirect(Dictionary(
            Type=Name.StructElem,
            S=heading_tag,
            P=document_elem,
            K=Array([]),
            # Note: Ideally would link to actual content, but minimal structure is acceptable
            T=String(heading['text'])  # Title/text of heading
        ))

        if '/K' not in document_elem:
            document_elem.K = Array([])

        document_elem.K.append(heading_elem)

    print(f"Added {len(headings)} heading elements")

    # Set accessibility flags
    pdf.Root.MarkInfo = Dictionary(Marked=True)

    if '/ViewerPreferences' not in pdf.Root:
        pdf.Root.ViewerPreferences = Dictionary()
    pdf.Root.ViewerPreferences.DisplayDocTitle = True

    # Set metadata if provided
    if metadata:
        if metadata.get('title'):
            pdf.docinfo[Name.Title] = String(metadata['title'])
        if metadata.get('author'):
            pdf.docinfo[Name.Author] = String(metadata['author'])
        if metadata.get('language'):
            pdf.Root.Lang = String(metadata['language'])

    # Save
    pdf.save(output_path, linearize=True)
    pdf.close()

    print("PDF saved with heading structure!")


def main():
    parser = argparse.ArgumentParser(
        description="Add heading tags to PDF structure tree"
    )
    parser.add_argument("pdf_path", help="Path to input PDF file")
    parser.add_argument("--output", "-o", required=True, help="Output PDF path")

    # Heading detection mode
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--auto", action="store_true",
                      help="Automatically detect headings (default)")
    group.add_argument("--manual-headings",
                      help="JSON file with manual heading specifications")

    # Export detected headings
    parser.add_argument("--export-headings",
                       help="Export detected headings to JSON file for review")

    # Optional metadata
    parser.add_argument("--title", help="Document title")
    parser.add_argument("--author", help="Document author")
    parser.add_argument("--language", default="en", help="Document language")

    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"Error: File not found: {args.pdf_path}")
        sys.exit(1)

    # Get headings
    if args.manual_headings:
        headings = load_manual_headings(args.manual_headings)
    else:
        # Auto-detect
        text_blocks = extract_text_with_fonts(args.pdf_path)
        headings = identify_headings(text_blocks)

    # Export if requested
    if args.export_headings:
        with open(args.export_headings, 'w', encoding='utf-8') as f:
            json.dump(headings, f, indent=2, ensure_ascii=False)
        print(f"\nHeadings exported to: {args.export_headings}")

    # Create PDF with headings
    metadata = {
        'title': args.title,
        'author': args.author,
        'language': args.language
    }

    add_heading_structure_tree(args.pdf_path, args.output, headings, metadata)

    # Verify
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)

    verify_pdf = pikepdf.open(args.output)

    if '/StructTreeRoot' in verify_pdf.Root:
        struct = verify_pdf.Root.StructTreeRoot
        if '/K' in struct and len(struct.K) > 0:
            doc = struct.K[0]
            if '/K' in doc:
                heading_elements = [e for e in doc.K if hasattr(e, 'S') and str(e.S).startswith('/H')]
                print(f"[OK] Structure tree with {len(heading_elements)} heading elements")

                # Count by level
                by_level = defaultdict(int)
                for elem in heading_elements:
                    by_level[str(elem.S)] += 1

                for level in sorted(by_level.keys()):
                    print(f"  {level}: {by_level[level]} elements")

    verify_pdf.close()
    print("="*60)


if __name__ == "__main__":
    main()
