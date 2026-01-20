# PDF Accessibility Standards

This document outlines the key accessibility standards and metadata requirements for PDF documents.

## PDF/UA (Universal Accessibility)

PDF/UA is the ISO standard (ISO 14289-1) for accessible PDF documents. Key requirements include:

### Required Metadata Fields

1. **Title** (`/Title`)
   - Descriptive title of the document
   - Should be human-readable and meaningful
   - Used by screen readers to identify the document

2. **Language** (`/Language`)
   - ISO 639-1 language code (e.g., "en", "es", "fr", "de")
   - Critical for screen readers to use correct pronunciation
   - Can specify primary and secondary languages

3. **Subject** (`/Subject`)
   - Brief description of document content
   - Helps users understand document purpose
   - Should be 1-2 sentences

4. **Keywords** (`/Keywords`)
   - Comma-separated tags describing content
   - Improves searchability
   - Should include document type, format, and content descriptors

5. **Author** (`/Author`)
   - Document creator or organization
   - Optional but recommended
   - Can be extracted from first page content or existing metadata
   - Common patterns: "by Name", "Author: Name", "Presenter: Name"

## Language Codes (ISO 639-1)

Common language codes:
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `zh` - Chinese
- `ja` - Japanese
- `ko` - Korean
- `ar` - Arabic
- `ru` - Russian
- `hi` - Hindi

## Document Type Classification

### Common Types

1. **Lecture** - Educational presentation or teaching material
2. **Instructions** - Step-by-step guides or manuals
3. **Workshop** - Training materials or hands-on exercises
4. **Report** - Analytical or summary documents
5. **Form** - Fillable documents requiring user input
6. **Presentation** - Slide-based visual content
7. **Article** - Written content for publication
8. **Brochure** - Marketing or informational material

## Format Classification

### Slides
- Typically <600 characters per page
- Contains bullet points or numbered lists
- Multiple pages with consistent layout
- Visual emphasis over continuous text

### Text Document
- Continuous prose format
- Longer paragraphs
- May include sections and chapters
- Emphasis on reading flow

## Content Tags

Recommended content-descriptive tags:

- **visual-content** - Contains diagrams, figures, charts, or images
- **tabular-data** - Contains tables or structured data
- **technical-content** - Programming, code, or technical specifications
- **mathematical-content** - Equations, formulas, theorems
- **academic** - Scholarly content with citations or references
- **brief** - Short documents (<500 words)
- **comprehensive** - Long-form documents (>5000 words)

## Accessibility Best Practices

1. **Always include Title and Language metadata**
2. **Use descriptive, meaningful titles**
3. **Specify language for multilingual documents**
4. **Include content-descriptive keywords**
5. **Use consistent subject descriptions**
6. **Tag document type for categorization**

## PDF Catalog Accessibility Flags

Beyond metadata fields, PDFs require specific flags in the document catalog for accessibility compliance:

### ViewerPreferences
- **DisplayDocTitle** - Must be set to `true`
- Displays document title in title bar instead of filename
- Required by WCAG 2.1 AA standards
- Checked by Anthology Ally and other accessibility validators

### MarkInfo
- **Marked** - Must be set to `true`
- Indicates PDF is a "Tagged PDF" with structural content
- Signals to assistive technology that structure information is available
- Note: Setting this flag alone doesn't create structure tags; it indicates intent

### Lang (Catalog Level)
- Document language must be specified in both:
  1. Metadata dictionary (`/Language`)
  2. Document catalog (`/Lang`)
- Catalog-level language setting takes precedence for screen readers

## Compliance Checking

A PDF meets basic accessibility metadata requirements if:
- `/Title` is present and non-empty
- `/Language` is specified with valid ISO 639-1 code in metadata
- `/Lang` is specified in document catalog
- `/Subject` provides meaningful description
- `/Keywords` includes relevant content tags
- `DisplayDocTitle` is set to `true` in ViewerPreferences
- `Marked` is set to `true` in MarkInfo

## Structure Tree Requirements

A "Tagged PDF" must have a structure tree that defines the logical structure of the document:

### StructTreeRoot
- Root element of the structure tree
- Contains Type = /StructTreeRoot
- Has K (Kids) array with structure elements
- Minimum: One root element (typically /Document)

### Structure Elements
Basic structure tree example:
```
StructTreeRoot
└── Document (S=/Document)
    ├── H1 (heading)
    ├── P (paragraph)
    ├── L (list)
    │   ├── LI (list item)
    │   └── LI (list item)
    └── Figure (image with alt text)
```

**Minimal Structure Tree:**
For basic compliance without full content tagging:
```
StructTreeRoot
└── Document
```

This minimal tree satisfies the "has structure" requirement but doesn't provide detailed semantic tagging of content.

## Anthology Ally Compliance

Anthology Ally (formerly Blackboard Ally) checks for WCAG 2.1 AA compliance:

**Metadata Requirements:**
- ✅ Document must have a title
- ✅ Title must be set to display (DisplayDocTitle = true)
- ✅ Document language must be specified
- ✅ Author should be present when available
- ✅ Structure tree must exist (StructTreeRoot)
- ✅ MarkInfo.Marked must be True

**Additional Checks (not addressed by this tool):**
- ⚠️ Semantic content tags (H1-H6, P, List, Table, etc.)
- ⚠️ Alt text for images
- ⚠️ Reading order
- ⚠️ Color contrast

**Result:** This tool provides a **minimal structure tree** that passes Anthology Ally's "has structure" check, but may not achieve perfect scores without detailed content tagging.
