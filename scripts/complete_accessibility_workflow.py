#!/usr/bin/env python3
"""
Complete PDF Accessibility Workflow

This script runs the complete workflow to make a PDF accessible:
1. Analyze content and generate metadata
2. Extract images and prompt for alt text
3. Create structure tree with Figure elements
4. Apply all accessibility flags

Requirements:
    pip install pypdf langdetect pikepdf Pillow anthropic

Usage:
    # With automatic alt text (requires ANTHROPIC_API_KEY)
    python complete_accessibility_workflow.py input.pdf --output accessible.pdf --auto-alt-text

    # With alt text from JSON file
    python complete_accessibility_workflow.py input.pdf --output accessible.pdf --alt-text-file alts.json

    # Interactive mode
    python complete_accessibility_workflow.py input.pdf --output accessible.pdf --interactive-alt-text

    # Skip alt text (only metadata and structure tree)
    python complete_accessibility_workflow.py input.pdf --output accessible.pdf --skip-images
"""

import sys
import json
import argparse
from pathlib import Path
import subprocess

# Import from other scripts
sys.path.insert(0, str(Path(__file__).parent))

try:
    from analyze_and_tag_pdf import analyze_pdf
    from add_alt_text_to_images import (
        extract_images_from_pdf,
        add_alt_text_auto,
        add_alt_text_interactive,
        add_alt_text_from_file,
        add_alt_text_to_pdf
    )
except ImportError as e:
    print(f"Error importing required scripts: {e}")
    print("Make sure all scripts are in the same directory.")
    sys.exit(1)


def run_complete_workflow(input_pdf, output_pdf, alt_text_mode='skip', alt_text_file=None):
    """
    Run the complete accessibility workflow.
    """
    print("="*70)
    print("COMPLETE PDF ACCESSIBILITY WORKFLOW")
    print("="*70)
    print(f"Input: {input_pdf}")
    print(f"Output: {output_pdf}")
    print()

    # Step 1: Analyze PDF content
    print("STEP 1: Analyzing PDF content...")
    print("-"*70)
    analysis = analyze_pdf(input_pdf)

    print(f"  Document Type: {analysis['document_type']}")
    print(f"  Format: {analysis['format']}")
    print(f"  Language: {analysis['primary_language']}")
    print(f"  Title: {analysis['suggested_title']}")
    print(f"  Author: {analysis['suggested_author'] or '(not detected)'}")
    print()

    # Step 2: Extract and process images
    if alt_text_mode != 'skip':
        print("STEP 2: Processing images for alt text...")
        print("-"*70)

        images = extract_images_from_pdf(input_pdf)

        if not images:
            print("  No images found. Skipping image processing.")
        else:
            if alt_text_mode == 'auto':
                images = add_alt_text_auto(images)
            elif alt_text_mode == 'interactive':
                images = add_alt_text_interactive(images)
            elif alt_text_mode == 'file' and alt_text_file:
                images = add_alt_text_from_file(images, alt_text_file)

            print()

            # Create PDF with alt text
            metadata = {
                'title': analysis['suggested_title'],
                'author': analysis['suggested_author'] or '',
                'subject': analysis['suggested_subject'],
                'keywords': analysis['suggested_keywords'],
                'language': analysis['primary_language']
            }

            add_alt_text_to_pdf(input_pdf, output_pdf, images, metadata)

    else:
        # No image processing - use enhance_pdf_accessibility
        print("STEP 2: Skipping image processing...")
        print("-"*70)
        print("  Using enhance_pdf_accessibility.py for structure tree only")

        from enhance_pdf_accessibility import enhance_pdf_accessibility

        metadata = {
            'title': analysis['suggested_title'],
            'author': analysis['suggested_author'] or '',
            'subject': analysis['suggested_subject'],
            'keywords': analysis['suggested_keywords'],
            'language': analysis['primary_language']
        }

        enhance_pdf_accessibility(input_pdf, output_pdf, metadata)

    # Step 3: Verification
    print()
    print("STEP 3: Verification...")
    print("-"*70)

    import pikepdf
    pdf = pikepdf.open(output_pdf)

    checks = {
        'StructTreeRoot': '/StructTreeRoot' in pdf.Root,
        'MarkInfo.Marked': pdf.Root.get('/MarkInfo', {}).get('/Marked', False),
        'DisplayDocTitle': pdf.Root.get('/ViewerPreferences', {}).get('/DisplayDocTitle', False),
        'Language': '/Lang' in pdf.Root,
        'Title': '/Title' in pdf.docinfo,
        'Author': '/Author' in pdf.docinfo
    }

    for check, result in checks.items():
        status = "[OK]" if result else "[MISSING]"
        print(f"  {status} {check}")

    # Count Figure elements if any
    if '/StructTreeRoot' in pdf.Root:
        try:
            struct_tree = pdf.Root.StructTreeRoot
            if '/K' in struct_tree and len(struct_tree.K) > 0:
                doc_elem = struct_tree.K[0]
                if '/K' in doc_elem:
                    figure_count = sum(1 for elem in doc_elem.K
                                     if hasattr(elem, 'S') and elem.S == '/Figure')
                    print(f"  [OK] Figure elements with alt text: {figure_count}")
        except:
            pass

    pdf.close()

    # Final summary
    print()
    print("="*70)
    if all(checks.values()):
        print("SUCCESS: PDF fully enhanced for accessibility!")
    else:
        print("PARTIAL: Some features may be missing")
    print("="*70)
    print(f"\nAccessible PDF created: {output_pdf}")

    return all(checks.values())


def main():
    parser = argparse.ArgumentParser(
        description="Complete PDF accessibility workflow"
    )
    parser.add_argument("pdf_path", help="Path to input PDF file")
    parser.add_argument("--output", "-o", required=True,
                       help="Output PDF path")

    # Alt text options
    alt_group = parser.add_mutually_exclusive_group()
    alt_group.add_argument("--auto-alt-text", action="store_true",
                          help="Auto-generate alt text using Claude API")
    alt_group.add_argument("--interactive-alt-text", action="store_true",
                          help="Interactively input alt text")
    alt_group.add_argument("--alt-text-file",
                          help="JSON file with alt text")
    alt_group.add_argument("--skip-images", action="store_true",
                          help="Skip image processing (metadata only)")

    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"Error: File not found: {args.pdf_path}")
        sys.exit(1)

    # Determine alt text mode
    if args.auto_alt_text:
        alt_text_mode = 'auto'
        alt_text_file = None
    elif args.interactive_alt_text:
        alt_text_mode = 'interactive'
        alt_text_file = None
    elif args.alt_text_file:
        alt_text_mode = 'file'
        alt_text_file = args.alt_text_file
    else:
        alt_text_mode = 'skip'
        alt_text_file = None

    success = run_complete_workflow(
        args.pdf_path,
        args.output,
        alt_text_mode,
        alt_text_file
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
