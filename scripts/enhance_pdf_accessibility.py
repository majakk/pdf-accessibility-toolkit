#!/usr/bin/env python3
"""
Enhanced PDF Accessibility Tool using pikepdf

This script adds structure tree and accessibility metadata to existing PDFs.
Use this AFTER running analyze_and_tag_pdf.py for maximum accessibility compliance.

Requirements:
    pip install pikepdf

Usage:
    python enhance_pdf_accessibility.py <input.pdf> --output <output.pdf> \
        --title "Title" --author "Author" --language "en"
"""

import sys
import argparse
from pathlib import Path

try:
    import pikepdf
    from pikepdf import Dictionary, Array, Name, String
except ImportError:
    print("Error: pikepdf is not installed. Run: pip install pikepdf")
    sys.exit(1)


def enhance_pdf_accessibility(input_path, output_path, metadata=None):
    """
    Enhance PDF with structure tree and full accessibility metadata.

    Args:
        input_path: Path to input PDF
        output_path: Path to output PDF
        metadata: Dict with title, author, subject, keywords, language
    """
    if metadata is None:
        metadata = {}

    print(f"Opening PDF: {input_path}")
    pdf = pikepdf.open(input_path)

    # Add structure tree
    print("Adding structure tree...")
    if '/StructTreeRoot' not in pdf.Root:
        # Create structure tree root
        struct_tree_root = pdf.make_indirect(Dictionary(
            Type=Name.StructTreeRoot,
            K=Array([]),
            ParentTree=Dictionary(Nums=Array([])),
            RoleMap=Dictionary()
        ))

        # Create document element
        document_elem = pdf.make_indirect(Dictionary(
            Type=Name.StructElem,
            S=Name.Document,
            P=struct_tree_root,
            K=Array([])
        ))

        struct_tree_root.K.append(document_elem)
        pdf.Root.StructTreeRoot = struct_tree_root
        print("  [OK] Structure tree added")
    else:
        print("  [OK] Structure tree already exists")

    # Set MarkInfo
    print("Setting MarkInfo...")
    pdf.Root.MarkInfo = Dictionary(Marked=True)
    print("  [OK] Marked = True")

    # Set ViewerPreferences
    print("Setting ViewerPreferences...")
    if '/ViewerPreferences' not in pdf.Root:
        pdf.Root.ViewerPreferences = Dictionary()
    pdf.Root.ViewerPreferences.DisplayDocTitle = True
    print("  [OK] DisplayDocTitle = True")

    # Set metadata
    if metadata.get('language'):
        print(f"Setting language: {metadata['language']}")
        pdf.Root.Lang = String(metadata['language'])

    if metadata.get('title'):
        print(f"Setting title: {metadata['title']}")
        pdf.docinfo[Name.Title] = String(metadata['title'])

    if metadata.get('author'):
        print(f"Setting author: {metadata['author']}")
        pdf.docinfo[Name.Author] = String(metadata['author'])

    if metadata.get('subject'):
        pdf.docinfo[Name.Subject] = String(metadata['subject'])

    if metadata.get('keywords'):
        pdf.docinfo[Name.Keywords] = String(metadata['keywords'])

    # Update XMP metadata
    print("Updating XMP metadata...")
    try:
        with pdf.open_metadata() as meta:
            if metadata.get('title'):
                meta['dc:title'] = metadata['title']
            if metadata.get('author'):
                meta['dc:creator'] = [metadata['author']]
            if metadata.get('subject'):
                meta['dc:description'] = metadata['subject']
            if metadata.get('keywords'):
                meta['pdf:Keywords'] = metadata['keywords']
            if metadata.get('language'):
                meta['dc:language'] = [metadata['language']]
        print("  [OK] XMP metadata updated")
    except Exception as e:
        print(f"  [WARNING] XMP metadata update failed: {e}")

    # Save
    print(f"\nSaving to: {output_path}")
    pdf.save(output_path, linearize=True)
    pdf.close()

    # Verify
    print("\nVerifying accessibility features...")
    verify_pdf = pikepdf.open(output_path)

    checks = {
        'StructTreeRoot': '/StructTreeRoot' in verify_pdf.Root,
        'Marked': verify_pdf.Root.get('/MarkInfo', {}).get('/Marked', False),
        'DisplayDocTitle': verify_pdf.Root.get('/ViewerPreferences', {}).get('/DisplayDocTitle', False),
        'Lang': '/Lang' in verify_pdf.Root
    }

    for check, result in checks.items():
        status = "[OK]" if result else "[MISSING]"
        print(f"  {status} {check}")

    verify_pdf.close()

    if all(checks.values()):
        print("\n" + "="*60)
        print("SUCCESS: PDF enhanced with accessibility features")
        print("="*60)
        return True
    else:
        print("\n" + "="*60)
        print("WARNING: Some accessibility features may be missing")
        print("="*60)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Enhance PDF with structure tree and accessibility metadata"
    )
    parser.add_argument("pdf_path", help="Path to input PDF file")
    parser.add_argument("--output", "-o", help="Output path (default: input_with_accessibility.pdf)")
    parser.add_argument("--title", help="Document title")
    parser.add_argument("--author", help="Document author")
    parser.add_argument("--subject", help="Document subject")
    parser.add_argument("--keywords", help="Document keywords")
    parser.add_argument("--language", default="en", help="Document language (ISO 639-1)")

    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"Error: File not found: {args.pdf_path}")
        sys.exit(1)

    output_path = args.output
    if not output_path:
        p = Path(args.pdf_path)
        output_path = str(p.parent / f"{p.stem}_with_accessibility{p.suffix}")

    metadata = {
        'title': args.title,
        'author': args.author,
        'subject': args.subject,
        'keywords': args.keywords,
        'language': args.language
    }

    # Remove None values
    metadata = {k: v for k, v in metadata.items() if v is not None}

    success = enhance_pdf_accessibility(args.pdf_path, output_path, metadata)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
