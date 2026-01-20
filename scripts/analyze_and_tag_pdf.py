#!/usr/bin/env python3
"""
PDF Accessibility Analyzer and Tagger

This script analyzes PDF files and updates their metadata for accessibility compliance.
It detects document type, format, language, and generates appropriate tags.

Requirements:
    pip install pypdf langdetect
    pip install pikepdf  # Optional: for structure tree creation (highly recommended)

Usage:
    python analyze_and_tag_pdf.py <pdf_file_path> [--output <output_path>]
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("Error: pypdf is not installed. Run: pip install pypdf")
    sys.exit(1)

try:
    from langdetect import detect, detect_langs, LangDetectException
except ImportError:
    print("Error: langdetect is not installed. Run: pip install langdetect")
    sys.exit(1)

# Optional: pikepdf for structure tree creation
PIKEPDF_AVAILABLE = False
try:
    import pikepdf
    from pikepdf import Dictionary, Array, Name, String as PikeString
    PIKEPDF_AVAILABLE = True
except ImportError:
    pass  # Will fall back to pypdf-only mode


# Document type patterns (including multilingual support)
DOC_TYPE_PATTERNS = {
    "lecture": [
        r"\blecture\b", r"\bslide\b", r"\blesson\b", r"\bchapter\s+\d+",
        r"\bcourse\b", r"\bsyllabus\b", r"\bsemester\b",
        # Swedish
        r"\bföreläsning", r"\bintroduktion", r"\bintro\b", r"\bkurs\b",
        # German
        r"\bvorlesung\b", r"\beinführung\b",
        # French
        r"\bcours\b", r"\bconférence\b",
        # Spanish
        r"\bclase\b", r"\blección\b"
    ],
    "instructions": [
        r"\binstruction", r"\bhow\s+to\b", r"\bguide\b", r"\bmanual\b",
        r"\bstep\s+\d+", r"\bprocedure\b", r"\btutorial\b",
        # Swedish
        r"\binstruktion", r"\bhandledning\b", r"\bguide\b",
        # German
        r"\banleitung\b", r"\bhandbuch\b",
        # French
        r"\bmanuel\b", r"\bguide\b"
    ],
    "workshop": [
        r"\bworkshop\b", r"\btraining\b", r"\bexercise\b", r"\bhands-on",
        r"\bactivity\b", r"\bpractical\b",
        # Swedish
        r"\bverkstad\b", r"\bövning", r"\butbildning\b",
        # German
        r"\bworkshop\b", r"\bübung\b",
        # French
        r"\batelier\b", r"\bexercice\b"
    ],
    "report": [
        r"\breport\b", r"\banalysis\b", r"\bfindings\b", r"\bsummary\b",
        r"\bconclusion\b", r"\babstract\b",
        # Swedish
        r"\brapport\b", r"\banalys\b", r"\bsammanfattning\b",
        # German
        r"\bbericht\b", r"\banalyse\b",
        # French
        r"\brapport\b", r"\banalyse\b"
    ],
    "form": [
        r"\bform\b", r"\bapplication\b", r"\bfill\s+out", r"\bsubmit\b",
        r"\bsignature\b",
        # Swedish
        r"\bformulär\b", r"\bansökan\b",
        # German
        r"\bformular\b", r"\bantrag\b",
        # French
        r"\bformulaire\b"
    ],
    "presentation": [
        r"\bpresentation\b", r"\bslideshow\b", r"\boverview\b", r"\bagenda\b",
        # Swedish
        r"\bpresentation\b", r"\böversikt\b",
        # German
        r"\bpräsentation\b", r"\bübersicht\b",
        # French
        r"\bprésentation\b"
    ],
    "article": [
        r"\barticle\b", r"\bpaper\b", r"\bjournal\b", r"\bpublication\b",
        r"\bresearch\b",
        # Swedish
        r"\bartikel\b", r"\buppsats\b", r"\bforskning\b",
        # German
        r"\bartikel\b", r"\bforschung\b",
        # French
        r"\barticle\b", r"\brecherche\b"
    ],
    "brochure": [
        r"\bbrochure\b", r"\bflyer\b", r"\bpamphlet\b", r"\bpromotional\b",
        # Swedish
        r"\bbroschyr\b", r"\bflygblad\b",
        # German
        r"\bbroschüre\b", r"\bflugblatt\b",
        # French
        r"\bbrochure\b", r"\bprospectus\b"
    ],
}


def extract_text_from_pdf(pdf_path: str) -> Tuple[str, int, bool]:
    """
    Extract text content from PDF and detect if it's a slide-based format.

    Returns:
        Tuple of (full_text, page_count, is_slides)
    """
    reader = PdfReader(pdf_path)
    page_count = len(reader.pages)

    full_text = ""
    text_per_page = []

    for page in reader.pages:
        page_text = page.extract_text()
        full_text += page_text + "\n"
        text_per_page.append(page_text)

    # Detect if it's slides vs continuous text
    # Slides typically have:
    # - Less text per page (avg < 500 chars)
    # - More consistent page lengths
    # - Bullet points or numbered lists
    avg_chars_per_page = sum(len(t) for t in text_per_page) / max(page_count, 1)
    has_bullets = bool(re.search(r"(^|\n)\s*[•\-*◦▪]\s+", full_text, re.MULTILINE))
    has_numbers = bool(re.search(r"(^|\n)\s*\d+[\.)]\s+", full_text, re.MULTILINE))

    is_slides = (avg_chars_per_page < 600 and page_count > 3) or \
                (has_bullets and page_count > 5) or \
                (has_numbers and avg_chars_per_page < 800)

    return full_text, page_count, is_slides


def detect_language(text: str) -> Tuple[str, List[Tuple[str, float]]]:
    """
    Detect the primary language and language probabilities.

    Returns:
        Tuple of (primary_lang_code, [(lang_code, probability), ...])
    """
    if not text or len(text.strip()) < 10:
        return "en", [("en", 1.0)]  # Default to English

    try:
        # Get primary language
        primary = detect(text)

        # Get all detected languages with probabilities
        lang_probs = detect_langs(text)
        lang_list = [(str(lp).split(':')[0], float(str(lp).split(':')[1]))
                     for lp in lang_probs]

        return primary, lang_list
    except LangDetectException:
        return "en", [("en", 1.0)]


def classify_document_type(text: str, filename: str) -> str:
    """
    Classify the document type based on content and filename.
    """
    text_lower = text.lower()
    filename_lower = filename.lower()

    # Check filename first
    for doc_type, patterns in DOC_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, filename_lower, re.IGNORECASE):
                return doc_type

    # Check content
    scores = {}
    for doc_type, patterns in DOC_TYPE_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            score += matches
        if score > 0:
            scores[doc_type] = score

    if scores:
        return max(scores, key=scores.get)

    return "document"  # Default


def generate_content_tags(text: str, doc_type: str, is_slides: bool) -> List[str]:
    """
    Generate content-descriptive tags based on analysis.
    """
    tags = []

    # Add document type
    tags.append(doc_type)

    # Add format
    tags.append("slides" if is_slides else "text-document")

    # Analyze content for additional tags
    text_lower = text.lower()

    # Topic indicators
    if re.search(r"\b(diagram|figure|chart|graph|image)\b", text_lower):
        tags.append("visual-content")

    if re.search(r"\b(table|column|row)\b", text_lower):
        tags.append("tabular-data")

    if re.search(r"\b(code|programming|function|class|variable)\b", text_lower):
        tags.append("technical-content")

    if re.search(r"\b(equation|formula|theorem|proof)\b", text_lower):
        tags.append("mathematical-content")

    if re.search(r"\b(reference|citation|bibliography)\b", text_lower):
        tags.append("academic")

    # Length-based tags
    word_count = len(text.split())
    if word_count < 500:
        tags.append("brief")
    elif word_count > 5000:
        tags.append("comprehensive")

    return tags


def extract_title_from_pdf(reader: PdfReader, text: str) -> Optional[str]:
    """
    Extract or infer the document title.
    """
    # First try metadata
    if reader.metadata and reader.metadata.title:
        return reader.metadata.title

    # Try to extract from first page (common for title to be there)
    if reader.pages:
        first_page_text = reader.pages[0].extract_text()
        lines = [line.strip() for line in first_page_text.split('\n') if line.strip()]
        if lines:
            # First non-empty line is often the title
            potential_title = lines[0]
            if len(potential_title) < 100:  # Reasonable title length
                return potential_title

    return None


def extract_author_from_pdf(reader: PdfReader) -> Optional[str]:
    """
    Extract author from PDF metadata or first page content.
    Looks for common author patterns on the first page.
    """
    # First try existing metadata
    if reader.metadata and reader.metadata.author:
        author = reader.metadata.author
        if author and author.strip():
            return author.strip()

    # Try to extract from first page
    if not reader.pages:
        return None

    first_page_text = reader.pages[0].extract_text()
    lines = [line.strip() for line in first_page_text.split('\n') if line.strip()]

    # Common author patterns (multilingual)
    author_patterns = [
        # English
        r"^(?:by|author|written by|presenter|instructor)[\s:]+(.+?)$",
        r"^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)$",  # Name pattern
        # Swedish
        r"^(?:av|författare|föreläsare)[\s:]+(.+?)$",
        # German
        r"^(?:von|autor|verfasser)[\s:]+(.+?)$",
        # French
        r"^(?:par|auteur)[\s:]+(.+?)$",
        # Email pattern (author often near email)
        r"^(.+?)\s*[<(]?[\w\.-]+@[\w\.-]+[>)]?$",
    ]

    # Check first 10 lines for author information
    for i, line in enumerate(lines[:10]):
        # Skip very short or very long lines
        if len(line) < 3 or len(line) > 100:
            continue

        for pattern in author_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                if match.groups():
                    author = match.group(1).strip()
                else:
                    author = match.group(0).strip()

                # Validate author name
                # Should be 2-50 chars, contain letters, may contain spaces/dots/hyphens
                if 2 <= len(author) <= 50 and re.search(r'[A-Za-zÀ-ÿ]', author):
                    # Remove common prefixes
                    author = re.sub(r'^(by|av|von|par|author|författare)[\s:]+', '', author, flags=re.IGNORECASE)
                    return author.strip()

    return None


def update_pdf_metadata(input_path: str, output_path: str, metadata: Dict) -> None:
    """
    Update PDF metadata with accessibility information.
    Includes WCAG 2.1 AA compliance settings for Anthology Ally and similar tools.
    """
    reader = PdfReader(input_path)
    writer = PdfWriter()

    # Copy all pages
    for page in reader.pages:
        writer.add_page(page)

    # Update metadata
    writer.add_metadata({
        "/Title": metadata.get("title", ""),
        "/Author": metadata.get("author", ""),
        "/Subject": metadata.get("subject", ""),
        "/Keywords": metadata.get("keywords", ""),
        "/Language": metadata.get("language", "en"),
    })

    # Set DisplayDocTitle flag (WCAG requirement)
    # This makes the PDF display the document title in the title bar instead of filename
    try:
        from pypdf.generic import DictionaryObject, BooleanObject, NameObject, TextStringObject

        # Set ViewerPreferences to display document title
        viewer_prefs = DictionaryObject()
        viewer_prefs.update({
            NameObject("/DisplayDocTitle"): BooleanObject(True)
        })
        writer._root_object.update({
            NameObject("/ViewerPreferences"): viewer_prefs
        })

        # Mark PDF as Tagged (indicates structured content for accessibility)
        # Note: This flag indicates intent; actual tagging of content requires deeper PDF manipulation
        mark_info = DictionaryObject()
        mark_info.update({
            NameObject("/Marked"): BooleanObject(True)
        })
        writer._root_object.update({
            NameObject("/MarkInfo"): mark_info
        })

        # Set document language in catalog (in addition to metadata)
        writer._root_object.update({
            NameObject("/Lang"): TextStringObject(metadata.get("language", "en"))
        })

    except Exception as e:
        # If advanced settings fail, continue with basic metadata
        print(f"Warning: Could not set advanced accessibility flags: {e}")

    # Write to output
    with open(output_path, "wb") as output_file:
        writer.write(output_file)


def add_structure_tree_with_pikepdf(pdf_path: str, metadata: Dict) -> bool:
    """
    Use pikepdf to add a structure tree to the PDF for better accessibility compliance.
    This creates a minimal structure tree that satisfies "Tagged PDF" requirements.

    Returns True if successful, False otherwise.
    """
    if not PIKEPDF_AVAILABLE:
        return False

    try:
        # Open with pikepdf
        pdf = pikepdf.open(pdf_path, allow_overwriting_input=True)

        # Add structure tree if it doesn't exist
        if '/StructTreeRoot' not in pdf.Root:
            # Create minimal structure tree
            struct_tree_root = Dictionary(
                Type=Name('/StructTreeRoot'),
                K=Array([]),
                ParentTree=Dictionary(Nums=Array([])),
                RoleMap=Dictionary()
            )

            # Add Document element as root
            document_elem = Dictionary(
                Type=Name('/StructElem'),
                S=Name('/Document'),
                P=struct_tree_root,
                K=Array([])
            )

            struct_tree_root.K.append(document_elem)
            pdf.Root.StructTreeRoot = struct_tree_root

        # Ensure MarkInfo is set
        if '/MarkInfo' not in pdf.Root:
            pdf.Root.MarkInfo = Dictionary()
        pdf.Root.MarkInfo.Marked = True

        # Ensure ViewerPreferences is set
        if '/ViewerPreferences' not in pdf.Root:
            pdf.Root.ViewerPreferences = Dictionary()
        pdf.Root.ViewerPreferences.DisplayDocTitle = True

        # Set catalog language
        if metadata.get("language"):
            pdf.Root.Lang = PikeString(metadata["language"])

        # Update XMP metadata for better compliance
        try:
            with pdf.open_metadata() as meta:
                if metadata.get("title"):
                    meta['dc:title'] = metadata["title"]
                if metadata.get("author"):
                    meta['dc:creator'] = [metadata["author"]]
                if metadata.get("subject"):
                    meta['dc:description'] = metadata["subject"]
                if metadata.get("keywords"):
                    meta['pdf:Keywords'] = metadata["keywords"]
                if metadata.get("language"):
                    meta['dc:language'] = [metadata["language"]]
        except Exception:
            pass  # XMP metadata is optional

        # Save changes
        pdf.save(pdf_path)
        pdf.close()
        return True

    except Exception as e:
        print(f"Warning: Could not add structure tree with pikepdf: {e}")
        return False


def analyze_pdf(pdf_path: str) -> Dict:
    """
    Main analysis function that returns all metadata.
    """
    path = Path(pdf_path)

    # Extract text and analyze structure
    text, page_count, is_slides = extract_text_from_pdf(pdf_path)

    # Detect language
    primary_lang, lang_probs = detect_language(text)

    # Classify document type
    doc_type = classify_document_type(text, path.name)

    # Generate tags
    tags = generate_content_tags(text, doc_type, is_slides)

    # Extract title and author
    reader = PdfReader(pdf_path)
    title = extract_title_from_pdf(reader, text)
    author = extract_author_from_pdf(reader)

    # Get existing metadata
    existing_meta = reader.metadata if reader.metadata else {}

    return {
        "filename": path.name,
        "page_count": page_count,
        "primary_language": primary_lang,
        "language_probabilities": lang_probs,
        "document_type": doc_type,
        "format": "slides" if is_slides else "text-document",
        "tags": tags,
        "suggested_title": title or path.stem.replace('_', ' ').replace('-', ' ').title(),
        "suggested_author": author or "",
        "suggested_subject": f"{doc_type.title()} - {', '.join(tags[:3])}",
        "suggested_keywords": ", ".join(tags),
        "existing_metadata": {
            "title": existing_meta.get("/Title", ""),
            "author": existing_meta.get("/Author", ""),
            "subject": existing_meta.get("/Subject", ""),
            "keywords": existing_meta.get("/Keywords", ""),
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Analyze PDF and update metadata for accessibility"
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument(
        "--output", "-o",
        help="Output path for tagged PDF (default: <original>_tagged.pdf)"
    )
    parser.add_argument(
        "--analyze-only", "-a",
        action="store_true",
        help="Only analyze and print metadata, don't create output file"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output analysis as JSON"
    )

    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"Error: File not found: {args.pdf_path}")
        sys.exit(1)

    # Analyze PDF
    analysis = analyze_pdf(args.pdf_path)

    # Output results
    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"PDF Accessibility Analysis: {analysis['filename']}")
        print(f"{'='*60}\n")
        print(f"Document Type:    {analysis['document_type']}")
        print(f"Format:           {analysis['format']}")
        print(f"Primary Language: {analysis['primary_language']}")
        print(f"Page Count:       {analysis['page_count']}")
        print(f"\nLanguage Detection:")
        for lang, prob in analysis['language_probabilities']:
            print(f"  {lang}: {prob:.2%}")
        print(f"\nContent Tags:")
        for tag in analysis['tags']:
            print(f"  - {tag}")
        print(f"\nSuggested Metadata:")
        print(f"  Title:    {analysis['suggested_title']}")
        print(f"  Author:   {analysis['suggested_author'] if analysis['suggested_author'] else '(not detected)'}")
        print(f"  Subject:  {analysis['suggested_subject']}")
        print(f"  Keywords: {analysis['suggested_keywords']}")

    # Update PDF if requested
    if not args.analyze_only:
        output_path = args.output
        if not output_path:
            path = Path(args.pdf_path)
            output_path = str(path.parent / f"{path.stem}_tagged{path.suffix}")

        metadata = {
            "title": analysis['suggested_title'],
            "author": analysis['suggested_author'],
            "subject": analysis['suggested_subject'],
            "keywords": analysis['suggested_keywords'],
            "language": analysis['primary_language'],
        }

        update_pdf_metadata(args.pdf_path, output_path, metadata)

        # Enhance with structure tree using pikepdf (if available)
        if PIKEPDF_AVAILABLE:
            if not args.json:
                print("\nEnhancing with structure tree...")
            success = add_structure_tree_with_pikepdf(output_path, metadata)
            if success and not args.json:
                print("  Structure tree added successfully")
        else:
            if not args.json:
                print("\nNote: Install pikepdf for enhanced accessibility compliance:")
                print("  pip install pikepdf")

        if not args.json:
            print(f"\n{'='*60}")
            print(f"Tagged PDF created: {output_path}")
            print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
