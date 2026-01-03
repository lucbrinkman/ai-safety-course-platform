# Skill: Clean Scraped Article

Clean a markdown file that was scraped from the web. This includes:
1. Fixing markdown formatting issues from trafilatura
2. Removing boilerplate (nav, comments, footer)

The file already has YAML frontmatter added by `extract_article.py`. Preserve it.

## Step 1: Preserve YAML Frontmatter

The file starts with YAML frontmatter like:
```yaml
---
title: "Article Title"
author: Author Name
date: January 2015
source_url: https://example.com/article
---
```

**Do not modify this.** Keep it exactly as-is.

## Step 2: Fix Markdown Formatting

Trafilatura produces malformed markdown. Fix these issues:

### Spaces Inside Asterisks
```
WRONG: *text * or * text* or **text ** or ** text**
RIGHT: *text* or **text**
```
Move spaces outside the asterisks.

### Bold Lines → Headers
Lines that are ONLY bold text and serve as section titles should become headers:
```
WRONG: **The Road to Superintelligence**
RIGHT: ## The Road to Superintelligence
```
Use similar headers to the ones found elsewhere in the article (if available). By default, good options are `##` for main sections, `###` for subsections.

**Exception:** Keep numbered items as bold: `**1) First point**`

### Missing Spaces After Formatting
```
WRONG: *word*next or **word**next
RIGHT: *word* next or **word** next
```

### Footnote Markers
Clean inline footnotes like `text.2` or `word11←` - remove them.

## Step 3: Remove Boilerplate

Remove:
- PDF/print version promos
- Editorial notes about the post
- Site navigation, menus, header links
- Sidebar content (related posts, categories, tags)
- Comments section
- Footer content (copyright, social links)
- Newsletter signups, share buttons
- "Read more" / "Related articles" sections
- Empty links like `[](/path)`

Preserve:
- YAML frontmatter (unchanged)
- All body content, inline links
- Images with alt text and URLs
- Blockquotes, code blocks

## Step 4: Write and Report

1. Write cleaned file back to the same path
2. Report what was fixed/removed (brief summary)
