# LLM_preprocesor_Large_files
Take gigantic file, make it easier for LLM to handle

# doc_prep (alpha)

**Goal:** Turn a single PDF / DOCX / TXT document into a folder of **“LLM-ready” artifacts**:
- cleaned full text
- chunked text segments
- chunk index
- basic metadata + overview

This is a **local, CLI-only tool** designed to be easy to hack on in VS Code.

---

## Features (alpha)

- Supports:
  - `.pdf` via **pypdf**
  - `.docx` via **python-docx**
  - `.txt` via plain file read
- Cleans and normalizes text:
  - normalizes newlines
  - removes obvious page-number-only lines
  - collapses excessive blank lines
- Estimates document size (tokens) and assigns a **tier**:
  - T0: ≤ 2k tokens
  - T1: 2k–10k tokens
  - T2: 10k–50k tokens
  - T3: > 50k tokens
- Chunks cleaned text into **LLM-friendly chunks**:
  - paragraphs are grouped until a max token budget is reached
  - optional paragraph-level overlap between chunks
- Writes a per-document artifact folder containing:
  - `raw_text.txt`
  - `metadata.json`
  - `chunk_index.json`
  - `overview.md`
  - `chunks/CH-XXXX.txt`

No LLM/API calls yet — this is purely **preprocessing**.

---

## Installation

### 1. Clone the repo

```bash
git clone <your-repo-url> doc_prep_tool
cd doc_prep_tool
