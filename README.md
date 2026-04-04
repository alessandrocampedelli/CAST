# CAST: Cinematic Analysis & Screenplay Transformer

Automated pipeline that converts film screenplays from PDF/HTML into TEI-XML and performs semantic analysis of locations, environments, and temporal patterns across scenes. Includes an interactive Streamlit dashboard for multi-film statistical comparison.

## Project Structure

```
CAST/
├── main.py                 # Main script (runs the full pipeline)
├── extract_txt.py          # Phase 1: Downloads from HF and extracts TXT from HTML/PDF
├── txt2tei.py              # Phase 2: Converts TXT → TEI-XML  
├── TEIAnalyzer.py          # Phase 3: Analyzes TEI screenplays
├── dashboard.py            # Phase 4: Interactive Streamlit dashboard
├── utils.py                # Utility functions for txt2tei
├── pyproject.toml          # Project dependencies (uv)
├── uv.lock                 # Lock file (uv)
├── .python-version         # Python version
├── README.md               # Documentation
├── input/                  # Downloaded automatically from Hugging Face
│   ├── pdf_scripts/        # PDF screenplay files
│   └── sites.txt           # HTML URLs to download (IMSDB)
├── txt_scripts/            # Intermediate TXT files (auto-generated)
├── tei_scripts/            # TEI XML files (auto-generated)
└── analysis/               # Analysis results (auto-generated)
    ├── screenplay_analysis.json
    └── screenplay_analysis_macro_stats.json
```

## Installation

### Prerequisites

Install `uv` (package manager):

```bash
# Linux/macOS
curl -Lsf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup

```bash
git clone https://github.com/alessandrocampedelli/CAST
cd CAST
uv sync
```

`uv sync` automatically installs all dependencies defined in `pyproject.toml`.

## Usage

### Automatic Execution (Recommended)

```bash
uv run python main.py
```

Automatically runs all four phases in sequence:

1. **Data download** from Hugging Face (PDFs + `sites.txt`)
2. **Text extraction** from PDF/HTML
3. **Conversion** to TEI-XML format
4. **Statistical analysis** of screenplays
5. **Dashboard launch** in the browser

### Input Data — Hugging Face

Input files (screenplay PDFs and `sites.txt`) are hosted on Hugging Face Datasets:

```
https://huggingface.co/datasets/campe03/CAST-screenplays
```

`extract_txt.py` downloads them automatically on first run. Files already present locally are skipped (no repeated downloads).

### Manual Execution (Advanced)

#### Phase 1: Download and TXT Extraction
```bash
uv run python extract_txt.py
```
- **Input**: PDFs and `sites.txt` downloaded from Hugging Face
- **Output**: TXT files in `txt_scripts/`

#### Phase 2: TEI-XML Conversion
```bash
uv run python txt2tei.py
```
- **Input**: TXT files in `txt_scripts/`
- **Output**: XML files in `tei_scripts/`

#### Phase 3: Statistical Analysis
```bash
uv run python TEIAnalyzer.py
```
- **Input**: XML files in `tei_scripts/`
- **Output**: JSON files in `analysis/`

#### Phase 4: Interactive Dashboard
```bash
uv run python -m streamlit run dashboard.py
```
- **Input**: JSON files from `analysis/`
- **Output**: Interactive web dashboard

## Input Format

### Supported Sources
- **PDF files**: Screenplay PDFs hosted on Hugging Face
- **IMSDB websites**: URLs listed in `sites.txt`, hosted on Hugging Face

Intermediate TXT files follow the standard screenplay format:

- **Location lines**: `INT. LIVING ROOM - DAY` or `EXT. STREET - NIGHT`
- **Speakers**: Uppercase names (e.g. `JOHN`, `MARY (CONT'D)`)
- **Dialogue**: Plain text after the character name
- **Stage directions**: Narrative descriptions

## Output Format

### TEI-XML Files
XML files follow the TEI (Text Encoding Initiative) standard:

```xml
<?xml version="1.0" encoding="utf-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Film Title</title>
      </titleStmt>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <div type="scene" n="1">
        <stage type="location">INT. LIVING ROOM - DAY</stage>
        <sp>
          <speaker>JOHN</speaker>
          <p>Hey, how are you?</p>
        </sp>
        <stage>John walks into the kitchen.</stage>
      </div>
    </body>
  </text>
</TEI>
```

### JSON Analysis Files
Statistics are saved in two files:

- `screenplay_analysis.json`: Detailed analysis for each individual film
- `screenplay_analysis_macro_stats.json`: Aggregated statistics across all films

## Features

### TEI-XML Conversion
#### Automatic Recognition
- **Scenes**: Identified via location lines (INT./EXT.)
- **Characters**: Uppercase names with continuation handling
- **Dialogue**: Text associated with characters
- **Descriptions**: Stage directions and scene indications

#### Smart Filters
- Removes page numbers
- Ignores headers and footers
- Skips cinematic transitions (`CUT TO:`, `FADE OUT`, etc.)
- Handles `CONTINUED` and `(MORE)` lines

### Statistical Analysis
#### Location Analysis
- **Type**: INT/EXT classification
- **Environment**: urban, suburban, rural, sea, mountain, desert, space, fantasy
- **Setting**: contemporary, natural, fantasy/sci-fi

#### Temporal Analysis
- **Time of day**: MORNING, DAY, EVENING, NIGHT
- **Seasons**: spring, summer, autumn, winter

#### Aggregated Statistics
- Percentage distribution for all parameters
- Cross-film comparisons
- Pattern and trend identification

### Interactive Dashboard
- **Pie charts**: INT/EXT distribution, time of day, seasons
- **Bar charts**: Environments, cross-film comparisons
- **Individual analysis**: Detailed breakdown per film
- **Comparative metrics**: Comparison against general averages
- **Responsive visualizations**: Interactive charts with Plotly

## Project Files

### `main.py`
Orchestrator script that runs the full pipeline in sequence using `sys.executable` to ensure the correct virtual environment is used throughout.

### `extract_txt.py`
Automatically downloads input data from Hugging Face (`campe03/CAST-screenplays`), then extracts text from PDFs (pdfminer) and HTML pages (IMSDB via requests and BeautifulSoup).

### `txt2tei.py`
Converts screenplay format to TEI-XML with intelligent parsing.

### `utils.py`
Complete library of functions for screenplay element recognition:
- `is_location_line()`: Identifies new scenes with multiple patterns
- `is_speaker()`: Recognizes characters and continuations
- `is_page_number()`, `is_header_line()`: Filters for irrelevant content
- `extract_title_from_filename()`: Title extraction
- And over 10 additional specialized functions

### `TEIAnalyzer.py`
Advanced analyzer that:
- Semantically classifies locations and temporality
- Calculates statistics for individual films and aggregates
- Generates structured JSON reports
- Uses keyword dictionaries and WordNet for automatic classification

### `dashboard.py`
Streamlit dashboard with:
- Multi-film aggregate visualizations
- Detailed analysis for individual films
- Interactive charts (Plotly)
- Comparative metrics
- Responsive interface

## License

Open source project for educational and research purposes.
