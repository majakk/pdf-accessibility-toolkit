# PDF Accessibility Enhancement Tool

Automatically enhance PDF accessibility by adding structure tags, alt text for images, and proper metadata. Designed to improve Anthology Ally and WCAG 2.1 AA compliance scores.

## Features

✅ **Heading Detection (H1-H6)** - Automatically detects and tags document structure
✅ **Image Alt Text** - Extracts images and adds descriptive alt text
✅ **Metadata Enhancement** - Auto-detects title, author, language, document type
✅ **Structure Tree Creation** - Creates proper PDF accessibility structure
✅ **Multiple Languages** - Supports English, Swedish, German, French, Spanish
✅ **Batch Processing** - Process multiple PDFs at once
✅ **Anthology Ally Optimized** - Addresses key compliance requirements

## Quick Start

### Installation

```bash
pip install pypdf langdetect pikepdf Pillow anthropic
```

**Note:** `anthropic` is optional - only needed for automatic alt text generation.

### Complete Accessibility Enhancement (Recommended)

```bash
python scripts/complete_accessibility_with_headings.py input.pdf \
    --output accessible.pdf \
    --skip-images
```

This adds:
- Heading tags (H1-H6) for document structure
- All metadata (title, author, language, subject, keywords)
- Accessibility flags (Marked, DisplayDocTitle, Lang)
- Structure tree

### With Automatic Alt Text (Optional)

```bash
export ANTHROPIC_API_KEY="your-key-here"
python scripts/complete_accessibility_with_headings.py input.pdf \
    --output accessible.pdf \
    --auto-alt-text
```

Adds alt text to all images using Claude AI vision.

## Scripts

### Core Scripts

1. **complete_accessibility_with_headings.py** ⭐ RECOMMENDED
   - All-in-one solution with heading detection and alt text
   - Best for Anthology Ally compliance

2. **analyze_and_tag_pdf.py**
   - Analyzes PDF content and detects metadata
   - Language detection, document type classification

3. **add_heading_tags.py**
   - Detects and tags headings (H1-H6)
   - Creates structure tree with heading elements

4. **add_alt_text_to_images.py**
   - Extracts images and adds alt text
   - Supports automatic (AI), interactive, or JSON file input

5. **enhance_pdf_accessibility.py**
   - Adds basic structure tree and accessibility flags
   - Simpler option without heading/image detection

## Usage Examples

### Single PDF with Headings

```bash
python scripts/complete_accessibility_with_headings.py lecture.pdf \
    --output lecture_accessible.pdf \
    --skip-images
```

### Batch Processing

```python
from pathlib import Path
import subprocess

for pdf in Path("pdfs/").glob("*.pdf"):
    output = pdf.parent / f"{pdf.stem}_accessible.pdf"
    subprocess.run([
        "python", "scripts/complete_accessibility_with_headings.py",
        str(pdf), "--output", str(output), "--skip-images"
    ])
```

### Alt Text from JSON

```bash
# Create alt text JSON file
echo '{"1": "Description for image 1", "2": "Description for image 2"}' > alts.json

# Apply to PDF
python scripts/add_alt_text_to_images.py input.pdf \
    --output output.pdf \
    --alt-text-file alts.json
```

## What Gets Tagged

### Heading Detection

Automatically detects headings based on:
- Font size and text characteristics
- Capitalization (Title Case, ALL CAPS)
- Text length (headings are typically short)
- Numbering patterns (1., 1.1, etc.)
- Common heading keywords

Heading levels assigned:
- **H1** - Main titles (very short, ALL CAPS)
- **H2** - Section headings (numbered 1, 2, 3)
- **H3** - Subsections (numbered 1.1, 2.1)
- **H4** - Minor subsections

### Metadata

- **Title** - Extracted from document or filename
- **Author** - Detected from first page content
- **Language** - ISO 639-1 code (auto-detected)
- **Subject** - Generated from document type and tags
- **Keywords** - Content-descriptive tags

### Accessibility Flags

- `DisplayDocTitle` = True
- `Marked` = True
- `Lang` = detected language
- Structure tree with semantic elements

## Multilingual Support

### Document Type Detection

Recognizes keywords in:
- English: lecture, instruction, workshop, report
- Swedish: föreläsning, introduktion, handledning, rapport
- German: Vorlesung, Anleitung, Bericht
- French: cours, manuel, rapport
- Spanish: clase, lección

### Author Detection

Recognizes patterns in:
- English: "by", "author", "presenter"
- Swedish: "av", "författare", "föreläsare"
- German: "von", "autor"
- French: "par", "auteur"

## Anthology Ally Compliance

### What This Tool Addresses

✅ Document metadata (Title, Author, Language)
✅ Heading structure (H1-H6 tags)
✅ Image alt text (Figure elements)
✅ Structure tree (StructTreeRoot)
✅ Accessibility flags (Marked, DisplayDocTitle)

### What's Not Addressed

⚠️ Paragraph tags (P elements)
⚠️ List tags (L, LI elements)
⚠️ Table tags (Table, TR, TD elements)
⚠️ Reading order optimization
⚠️ Color contrast issues

**Result:** Addresses the most impactful accessibility requirements for significant score improvement.

## Requirements

- Python 3.7+
- pypdf (PDF reading/writing)
- langdetect (language detection)
- pikepdf (advanced PDF manipulation)
- Pillow (image processing)
- anthropic (optional - for automatic alt text)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or pull request.

## Acknowledgments

Built to improve PDF accessibility compliance for educational institutions using Anthology Ally and WCAG 2.1 AA standards.
