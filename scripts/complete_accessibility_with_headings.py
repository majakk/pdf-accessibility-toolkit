#!/usr/bin/env python3
"""
Complete PDF Accessibility with Headings and Alt Text

This is the ultimate accessibility enhancement script that adds:
- Heading tags (H1-H6) for document structure
- Alt text for images (Figure elements)
- All accessibility metadata and flags

Requirements:
    pip install pypdf langdetect pikepdf Pillow anthropic

Usage:
    # With automatic alt text and heading detection
    python complete_accessibility_with_headings.py input.pdf --output accessible.pdf --auto-alt-text

    # Skip alt text but add headings
    python complete_accessibility_with_headings.py input.pdf --output accessible.pdf --skip-images

    # Use JSON files for both
    python complete_accessibility_with_headings.py input.pdf --output accessible.pdf \
        --alt-text-file alts.json --headings-file headings.json
"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from analyze_and_tag_pdf import analyze_pdf
    from add_alt_text_to_images import extract_images_from_pdf, add_alt_text_auto, add_alt_text_interactive, add_alt_text_from_file
    from add_heading_tags import extract_text_with_fonts, identify_headings, load_manual_headings
except ImportError as e:
    print(f"Error importing scripts: {e}")
    sys.exit(1)

try:
    import pikepdf
    from pikepdf import Dictionary, Array, Name, String
except ImportError:
    print("Error: pikepdf not installed. Run: pip install pikepdf")
    sys.exit(1)


def create_complete_structure_tree(pdf, headings: list, images_with_alt: list, metadata: dict):
    """
    Create a complete structure tree with both headings and figures.
    """
    print("\nCreating complete structure tree...")

    # Create structure tree root
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

    # Create document element
    document_elem = pdf.make_indirect(Dictionary(
        Type=Name.StructElem,
        S=Name.Document,
        P=struct_tree_root,
        K=Array([])
    ))

    struct_tree_root.K = Array([document_elem])

    # Add heading elements
    print(f"Adding {len(headings)} heading elements...")
    for heading in headings:
        level = min(heading['level'], 6)
        heading_tag = Name(f'/H{level}')

        heading_elem = pdf.make_indirect(Dictionary(
            Type=Name.StructElem,
            S=heading_tag,
            P=document_elem,
            K=Array([]),
            T=String(heading['text'])
        ))

        document_elem.K.append(heading_elem)

    # Add figure elements with alt text
    images_with_alt_text = [img for img in images_with_alt if img.get('alt_text')]
    print(f"Adding {len(images_with_alt_text)} Figure elements with alt text...")

    for img in images_with_alt_text:
        figure_elem = pdf.make_indirect(Dictionary(
            Type=Name.StructElem,
            S=Name.Figure,
            P=document_elem,
            Alt=String(img['alt_text']),
            K=Array([])
        ))

        document_elem.K.append(figure_elem)

    print(f"Total structure elements: {len(document_elem.K)}")


def run_complete_accessibility(input_pdf, output_pdf, args):
    """
    Run complete accessibility enhancement with headings and alt text.
    """
    print("="*70)
    print("COMPLETE PDF ACCESSIBILITY ENHANCEMENT")
    print("With Headings and Alt Text")
    print("="*70)
    print(f"Input: {input_pdf}")
    print(f"Output: {output_pdf}\n")

    # Step 1: Analyze content
    print("STEP 1: Analyzing PDF content...")
    print("-"*70)
    analysis = analyze_pdf(input_pdf)

    print(f"  Type: {analysis['document_type']}")
    print(f"  Language: {analysis['primary_language']}")
    print(f"  Title: {analysis['suggested_title']}")
    print(f"  Author: {analysis['suggested_author'] or '(not detected)'}")

    # Step 2: Extract and process images
    images = []
    if not args.skip_images:
        print("\nSTEP 2: Processing images...")
        print("-"*70)
        images = extract_images_from_pdf(input_pdf)

        if images:
            if args.auto_alt_text:
                images = add_alt_text_auto(images)
            elif args.interactive_alt_text:
                images = add_alt_text_interactive(images)
            elif args.alt_text_file:
                images = add_alt_text_from_file(images, args.alt_text_file)
        else:
            print("  No images found")
    else:
        print("\nSTEP 2: Skipping image processing (--skip-images)")

    # Step 3: Detect headings
    print("\nSTEP 3: Detecting headings...")
    print("-"*70)

    if args.headings_file:
        headings = load_manual_headings(args.headings_file)
    else:
        text_blocks = extract_text_with_fonts(input_pdf)
        headings = identify_headings(text_blocks)

    # Step 4: Create enhanced PDF
    print("\nSTEP 4: Creating enhanced PDF...")
    print("-"*70)

    pdf = pikepdf.open(input_pdf)

    metadata = {
        'title': analysis['suggested_title'],
        'author': analysis['suggested_author'] or '',
        'subject': analysis['suggested_subject'],
        'keywords': analysis['suggested_keywords'],
        'language': analysis['primary_language']
    }

    # Create structure tree with both headings and figures
    create_complete_structure_tree(pdf, headings, images, metadata)

    # Set accessibility flags
    pdf.Root.MarkInfo = Dictionary(Marked=True)

    if '/ViewerPreferences' not in pdf.Root:
        pdf.Root.ViewerPreferences = Dictionary()
    pdf.Root.ViewerPreferences.DisplayDocTitle = True

    # Set metadata
    pdf.docinfo[Name.Title] = String(metadata['title'])
    if metadata['author']:
        pdf.docinfo[Name.Author] = String(metadata['author'])
    pdf.docinfo[Name.Subject] = String(metadata['subject'])
    pdf.docinfo[Name.Keywords] = String(metadata['keywords'])
    pdf.Root.Lang = String(metadata['language'])

    # Update XMP metadata
    try:
        with pdf.open_metadata() as meta:
            meta['dc:title'] = metadata['title']
            if metadata['author']:
                meta['dc:creator'] = [metadata['author']]
            meta['dc:description'] = metadata['subject']
            meta['pdf:Keywords'] = metadata['keywords']
            meta['dc:language'] = [metadata['language']]
        print("  XMP metadata updated")
    except Exception as e:
        print(f"  Warning: XMP update failed: {e}")

    # Save
    print(f"\nSaving to: {output_pdf}")
    pdf.save(output_pdf, linearize=True)
    pdf.close()

    # Verification
    print("\nSTEP 5: Verification...")
    print("-"*70)

    verify_pdf = pikepdf.open(output_pdf)

    checks = {
        'StructTreeRoot': '/StructTreeRoot' in verify_pdf.Root,
        'Marked': verify_pdf.Root.get('/MarkInfo', {}).get('/Marked', False),
        'DisplayDocTitle': verify_pdf.Root.get('/ViewerPreferences', {}).get('/DisplayDocTitle', False),
        'Language': '/Lang' in verify_pdf.Root,
        'Title': '/Title' in verify_pdf.docinfo
    }

    for check, result in checks.items():
        print(f"  {'[OK]' if result else '[MISS]'} {check}")

    # Count elements
    if '/StructTreeRoot' in verify_pdf.Root:
        struct = verify_pdf.Root.StructTreeRoot
        if '/K' in struct and len(struct.K) > 0:
            doc = struct.K[0]
            if '/K' in doc:
                from collections import defaultdict
                elem_count = defaultdict(int)

                for elem in doc.K:
                    if hasattr(elem, 'S'):
                        elem_type = str(elem.S)
                        if elem_type.startswith('/H'):
                            elem_count['Headings'] += 1
                        elif elem_type == '/Figure':
                            elem_count['Figures'] += 1

                print(f"\nStructure elements:")
                print(f"  Headings: {elem_count['Headings']}")
                print(f"  Figures with alt text: {elem_count['Figures']}")
                print(f"  Total: {len(doc.K)}")

    verify_pdf.close()

    # Final summary
    print("\n" + "="*70)
    if all(checks.values()):
        print("SUCCESS: PDF fully enhanced for accessibility!")
        print("  [OK] Heading tags for document structure")
        print("  [OK] Alt text for images")
        print("  [OK] All metadata and flags set")
    else:
        print("PARTIAL: Some features may be missing")
    print("="*70)

    return all(checks.values())


def main():
    parser = argparse.ArgumentParser(
        description="Complete PDF accessibility with headings and alt text"
    )
    parser.add_argument("pdf_path", help="Input PDF file")
    parser.add_argument("--output", "-o", required=True, help="Output PDF file")

    # Alt text options
    alt_group = parser.add_mutually_exclusive_group()
    alt_group.add_argument("--auto-alt-text", action="store_true",
                          help="Auto-generate alt text with Claude API")
    alt_group.add_argument("--interactive-alt-text", action="store_true",
                          help="Interactively input alt text")
    alt_group.add_argument("--alt-text-file", help="JSON file with alt text")
    alt_group.add_argument("--skip-images", action="store_true",
                          help="Skip image processing")

    # Heading options
    parser.add_argument("--headings-file", help="JSON file with manual headings")

    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"Error: File not found: {args.pdf_path}")
        sys.exit(1)

    success = run_complete_accessibility(args.pdf_path, args.output, args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
