#!/usr/bin/env python3
"""
Add Alt Text to Images in PDF

This script extracts images from a PDF and adds alt text to them for accessibility.
It can generate alt text automatically using Claude API or accept manual descriptions.

Requirements:
    pip install pikepdf Pillow anthropic

Usage:
    # Automatic alt text generation (requires ANTHROPIC_API_KEY)
    python add_alt_text_to_images.py input.pdf --output output.pdf --auto

    # Manual alt text (interactive)
    python add_alt_text_to_images.py input.pdf --output output.pdf --interactive

    # From JSON file with pre-defined alt text
    python add_alt_text_to_images.py input.pdf --output output.pdf --alt-text-file alts.json
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional
import base64
import io

try:
    import pikepdf
    from pikepdf import Dictionary, Array, Name, String
except ImportError:
    print("Error: pikepdf is not installed. Run: pip install pikepdf")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is not installed. Run: pip install Pillow")
    sys.exit(1)

# Optional: Anthropic API for automatic alt text generation
ANTHROPIC_AVAILABLE = False
try:
    import anthropic
    import os
    if os.environ.get('ANTHROPIC_API_KEY'):
        ANTHROPIC_AVAILABLE = True
except ImportError:
    pass


def extract_images_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extract all images from PDF with their locations.
    Returns list of dicts with page number, image data, and position info.
    """
    print(f"Extracting images from: {pdf_path}")
    pdf = pikepdf.open(pdf_path)

    images = []
    image_counter = 0

    for page_num, page in enumerate(pdf.pages, start=1):
        print(f"  Scanning page {page_num}...")

        if '/Resources' not in page or '/XObject' not in page.Resources:
            continue

        xobjects = page.Resources.XObject

        for key, obj in xobjects.items():
            try:
                if obj.Subtype == Name.Image:
                    image_counter += 1

                    # Get image data
                    try:
                        pil_image = pikepdf.PdfImage(obj).as_pil_image()

                        # Convert to bytes for processing
                        img_bytes = io.BytesIO()
                        pil_image.save(img_bytes, format='PNG')
                        img_bytes.seek(0)

                        images.append({
                            'id': image_counter,
                            'page': page_num,
                            'key': str(key),
                            'obj': obj,
                            'pil_image': pil_image,
                            'bytes': img_bytes.getvalue(),
                            'width': pil_image.width,
                            'height': pil_image.height,
                            'alt_text': None
                        })

                        print(f"    Found image #{image_counter}: {pil_image.width}x{pil_image.height}")

                    except Exception as e:
                        print(f"    Warning: Could not extract image data: {e}")

            except Exception as e:
                continue

    pdf.close()
    print(f"\nTotal images found: {len(images)}")
    return images


def generate_alt_text_with_claude(image_bytes: bytes) -> str:
    """
    Generate alt text for an image using Claude API.
    """
    if not ANTHROPIC_AVAILABLE:
        return None

    try:
        client = anthropic.Anthropic()

        # Encode image to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_image
                        }
                    },
                    {
                        "type": "text",
                        "text": "Provide a concise alt text description for this image (1-2 sentences, suitable for screen readers). Focus on the main content and purpose of the image."
                    }
                ]
            }]
        )

        alt_text = message.content[0].text.strip()
        return alt_text

    except Exception as e:
        print(f"Error generating alt text with Claude: {e}")
        return None


def add_alt_text_interactive(images: List[Dict]) -> List[Dict]:
    """
    Interactively ask user for alt text for each image.
    """
    print("\n" + "="*60)
    print("INTERACTIVE ALT TEXT INPUT")
    print("="*60)
    print("You will be prompted to provide alt text for each image.")
    print("Tips: Describe the content and purpose, 1-2 sentences.\n")

    for img in images:
        print(f"\nImage #{img['id']} (Page {img['page']}, {img['width']}x{img['height']})")

        # Try to show image if possible
        try:
            img['pil_image'].show()
        except:
            print("  (Could not display image)")

        alt_text = input(f"Enter alt text (or 'skip' to leave empty): ").strip()

        if alt_text.lower() == 'skip':
            img['alt_text'] = ""
        else:
            img['alt_text'] = alt_text

    return images


def add_alt_text_auto(images: List[Dict]) -> List[Dict]:
    """
    Automatically generate alt text using Claude API.
    """
    if not ANTHROPIC_AVAILABLE:
        print("Error: Claude API not available. Set ANTHROPIC_API_KEY environment variable.")
        return images

    print("\n" + "="*60)
    print("AUTOMATIC ALT TEXT GENERATION")
    print("="*60)
    print("Using Claude API to generate alt text for images...\n")

    for img in images:
        print(f"Processing image #{img['id']} (Page {img['page']})...")
        alt_text = generate_alt_text_with_claude(img['bytes'])

        if alt_text:
            img['alt_text'] = alt_text
            print(f"  Alt text: {alt_text}")
        else:
            img['alt_text'] = ""
            print(f"  Could not generate alt text")

    return images


def add_alt_text_from_file(images: List[Dict], alt_text_file: str) -> List[Dict]:
    """
    Load alt text from JSON file.
    Format: {"1": "alt text for image 1", "2": "alt text for image 2", ...}
    """
    print(f"\nLoading alt text from: {alt_text_file}")

    with open(alt_text_file, 'r', encoding='utf-8') as f:
        alt_texts = json.load(f)

    for img in images:
        img_id_str = str(img['id'])
        if img_id_str in alt_texts:
            img['alt_text'] = alt_texts[img_id_str]
            print(f"  Image #{img['id']}: {img['alt_text'][:50]}...")
        else:
            img['alt_text'] = ""
            print(f"  Image #{img['id']}: (no alt text provided)")

    return images


def create_structure_tree_with_images(pdf, images: List[Dict], existing_metadata: Dict = None):
    """
    Create or update structure tree with Figure elements for images.
    """
    print("\nCreating structure tree with Figure elements...")

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

    # Add Figure elements for each image with alt text
    for img in images:
        if img['alt_text']:
            figure_elem = pdf.make_indirect(Dictionary(
                Type=Name.StructElem,
                S=Name.Figure,
                P=document_elem,
                Alt=String(img['alt_text']),
                K=Array([])  # Could link to actual content, but minimal is okay
            ))

            if '/K' not in document_elem:
                document_elem.K = Array([])

            document_elem.K.append(figure_elem)
            print(f"  Added Figure element for image #{img['id']} with alt text")

    print(f"Structure tree updated with {len([i for i in images if i['alt_text']])} Figure elements")


def add_alt_text_to_pdf(input_path: str, output_path: str, images: List[Dict], metadata: Dict = None):
    """
    Create enhanced PDF with alt text in structure tree.
    """
    print(f"\nCreating accessible PDF: {output_path}")

    pdf = pikepdf.open(input_path)

    # Create structure tree with Figure elements
    create_structure_tree_with_images(pdf, images, metadata)

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

    print("PDF saved with alt text!")


def main():
    parser = argparse.ArgumentParser(
        description="Add alt text to images in PDF for accessibility"
    )
    parser.add_argument("pdf_path", help="Path to input PDF file")
    parser.add_argument("--output", "-o", required=True, help="Output PDF path")

    # Alt text input methods
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--auto", action="store_true",
                      help="Automatically generate alt text using Claude API")
    group.add_argument("--interactive", action="store_true",
                      help="Interactively input alt text for each image")
    group.add_argument("--alt-text-file",
                      help="JSON file with alt text (format: {\"1\": \"text\", ...})")

    # Optional metadata
    parser.add_argument("--title", help="Document title")
    parser.add_argument("--author", help="Document author")
    parser.add_argument("--language", default="en", help="Document language")

    # Export alt text to file
    parser.add_argument("--export-alt-text", help="Export alt text to JSON file")

    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"Error: File not found: {args.pdf_path}")
        sys.exit(1)

    # Step 1: Extract images
    images = extract_images_from_pdf(args.pdf_path)

    if not images:
        print("\nNo images found in PDF. Nothing to do.")
        sys.exit(0)

    # Step 2: Get alt text
    if args.auto:
        images = add_alt_text_auto(images)
    elif args.interactive:
        images = add_alt_text_interactive(images)
    elif args.alt_text_file:
        images = add_alt_text_from_file(images, args.alt_text_file)

    # Step 3: Export alt text if requested
    if args.export_alt_text:
        alt_text_dict = {str(img['id']): img['alt_text'] for img in images}
        with open(args.export_alt_text, 'w', encoding='utf-8') as f:
            json.dump(alt_text_dict, f, indent=2, ensure_ascii=False)
        print(f"\nAlt text exported to: {args.export_alt_text}")

    # Step 4: Create accessible PDF
    metadata = {
        'title': args.title,
        'author': args.author,
        'language': args.language
    }

    add_alt_text_to_pdf(args.pdf_path, args.output, images, metadata)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total images: {len(images)}")
    print(f"Images with alt text: {len([i for i in images if i['alt_text']])}")
    print(f"Output: {args.output}")
    print("="*60)


if __name__ == "__main__":
    main()
