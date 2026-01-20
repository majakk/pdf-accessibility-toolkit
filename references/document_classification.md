# Document Classification Guide

This document provides detailed patterns and heuristics for classifying PDF documents by type and format.

## Multilingual Support

The classification system supports multiple languages for document type detection:

- **English** - lecture, slide, instruction, guide, workshop, training, report, form, presentation, article, brochure
- **Swedish** - föreläsning, introduktion, kurs, instruktion, handledning, verkstad, övning, rapport, formulär, presentation, artikel, broschyr
- **German** - Vorlesung, Einführung, Anleitung, Handbuch, Workshop, Übung, Bericht, Formular, Präsentation, Artikel, Broschüre
- **French** - cours, conférence, manuel, guide, atelier, exercice, rapport, formulaire, présentation, article, brochure
- **Spanish** - clase, lección (partial support)

Keywords in any of these languages will contribute to document type classification.

## Document Type Detection

### Lecture
**Indicators:**
- Keywords: "lecture", "slide", "lesson", "chapter", "course", "syllabus", "semester"
- Structure: Numbered slides or sections
- Content: Educational material with learning objectives
- Format: Often slide-based with bullet points

**Example filenames:**
- `lecture_01.pdf`
- `CS101_Lecture_Notes.pdf`
- `Introduction_to_Physics_Slides.pdf`

### Instructions
**Indicators:**
- Keywords: "instruction", "how to", "guide", "manual", "step", "procedure", "tutorial"
- Structure: Numbered or bulleted steps
- Content: Imperative language ("do this", "follow these steps")
- Format: Can be slides or text document

**Example filenames:**
- `user_manual.pdf`
- `installation_guide.pdf`
- `quick_start_instructions.pdf`

### Workshop
**Indicators:**
- Keywords: "workshop", "training", "exercise", "hands-on", "activity", "practical"
- Structure: Sections for activities and exercises
- Content: Interactive elements, practice problems
- Format: Mixed format with instructions and worksheets

**Example filenames:**
- `python_workshop.pdf`
- `team_building_exercises.pdf`
- `data_analysis_training.pdf`

### Report
**Indicators:**
- Keywords: "report", "analysis", "findings", "summary", "conclusion", "abstract"
- Structure: Executive summary, body, conclusions
- Content: Data, analysis, recommendations
- Format: Typically text document

**Example filenames:**
- `quarterly_report.pdf`
- `market_analysis.pdf`
- `research_findings.pdf`

### Form
**Indicators:**
- Keywords: "form", "application", "fill out", "submit", "signature"
- Structure: Fields for user input
- Content: Blank spaces, checkboxes, signature lines
- Format: Structured layout with form fields

**Example filenames:**
- `application_form.pdf`
- `registration.pdf`
- `tax_form.pdf`

### Presentation
**Indicators:**
- Keywords: "presentation", "slideshow", "overview", "agenda"
- Structure: Slides with titles and content sections
- Content: High-level overview, minimal text per slide
- Format: Always slide-based

**Example filenames:**
- `company_overview.pdf`
- `project_presentation.pdf`
- `sales_pitch.pdf`

### Article
**Indicators:**
- Keywords: "article", "paper", "journal", "publication", "research"
- Structure: Abstract, introduction, methodology, results, discussion
- Content: Academic or professional writing
- Format: Text document with citations

**Example filenames:**
- `research_paper.pdf`
- `journal_article.pdf`
- `white_paper.pdf`

### Brochure
**Indicators:**
- Keywords: "brochure", "flyer", "pamphlet", "promotional"
- Structure: Visual layout with images and short text
- Content: Marketing material, product information
- Format: Often visually designed pages

**Example filenames:**
- `product_brochure.pdf`
- `company_flyer.pdf`
- `event_pamphlet.pdf`

## Format Detection (Slides vs Text Document)

### Slides Format
**Characteristics:**
- Average characters per page: <600
- Multiple pages (typically >3)
- Contains bullet points (•, -, *, ◦, ▪)
- Contains numbered lists (1., 2., 3.)
- Short paragraphs or phrases
- Consistent page layout
- Visual elements emphasized

**Detection heuristics:**
```
is_slides = (avg_chars_per_page < 600 AND page_count > 3) OR
            (has_bullets AND page_count > 5) OR
            (has_numbers AND avg_chars_per_page < 800)
```

### Text Document Format
**Characteristics:**
- Average characters per page: >600
- Continuous prose
- Longer paragraphs
- Narrative flow between pages
- Fewer visual elements
- Traditional document structure

**Detection heuristics:**
```
is_text_document = NOT is_slides
```

## Content Tags Detection

### Visual Content
**Indicators:**
- Keywords: "diagram", "figure", "chart", "graph", "image", "illustration"
- Often references like "see Figure 1" or "as shown in the chart"

### Tabular Data
**Indicators:**
- Keywords: "table", "column", "row", "cell"
- Structured data presentation
- References like "Table 1" or "as shown in the table"

### Technical Content
**Indicators:**
- Keywords: "code", "programming", "function", "class", "variable", "API", "algorithm"
- Contains code snippets or technical specifications
- Programming language names (Python, Java, C++, etc.)

### Mathematical Content
**Indicators:**
- Keywords: "equation", "formula", "theorem", "proof", "lemma", "proposition"
- Mathematical symbols and notation
- Technical mathematical language

### Academic
**Indicators:**
- Keywords: "reference", "citation", "bibliography", "et al.", "ibid"
- Formal academic writing style
- Footnotes or endnotes
- Reference section

## Classification Algorithm

1. **Extract text** from PDF
2. **Check filename** for type indicators (quick win)
3. **Analyze content** using keyword patterns
4. **Score each type** based on pattern matches
5. **Select highest scoring type** or default to "document"
6. **Detect format** (slides vs text) using structural heuristics
7. **Generate content tags** based on content analysis
8. **Combine results** into comprehensive classification
