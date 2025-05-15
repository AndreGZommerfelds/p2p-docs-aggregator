# P2P Documentation Scraper

A Python tool that scrapes P2P.org documentation, downloads Markdown files concurrently, and aggregates them into a single, navigable document with table of contents.

**GitHub Repository**: [p2p-docs-aggregator](https://github.com/AndreGZommerfelds/p2p-docs-aggregator)

## Overview

This script:

1. Fetches a list of Markdown links from `https://docs.p2p.org/llms.txt`
2. Downloads all linked Markdown files concurrently
3. Saves individual Markdown files in a `markdown_files` directory
4. Aggregates all content into a single Markdown file with a table of contents
5. Logs detailed information about the scraping process

## Requirements

- Python 3.6+
- Required packages:
  - `requests` (required for both script versions)
  - `tqdm` (required only for the main script)

## Installation

1. Clone this repository:

   ```
   git clone <repository-url>
   cd p2p-docs-llm
   ```

2. Install required packages:

   ```
   pip install -r requirements.txt
   ```

   Or for minimal installation:

   ```
   pip install requests
   ```

## Usage

There are two script versions available:

### 1. Main Script (with progress bar)

```
python scrape_p2p_docs.py
```

This version uses `tqdm` for a nice progress bar and provides the most detailed progress tracking.

### 2. Simple Script (no extra dependencies)

```
python scrape_p2p_docs_simple.py
```

This version only requires `requests` and provides basic progress tracking in the terminal.

### Bash Script

For convenience, you can also use the provided shell script, which sets up a virtual environment and installs dependencies:

```
./run_scraper.sh [OPTIONS]
```

The shell script supports the following options:

- `-h, --help`: Show help message and exit
- `-s, --simple`: Use the simple version (no tqdm dependency)
- `-m, --minimal`: Use minimal dependencies (no tqdm)

Examples:

```
./run_scraper.sh                    # Run the full version with all dependencies
./run_scraper.sh --simple           # Run the simple script version
./run_scraper.sh --minimal          # Use minimal dependencies
./run_scraper.sh --simple --minimal # Run simple script with minimal dependencies
```

## Output

The script produces the following:

- `p2p_aggregated_docs.md`: The aggregated documentation file
- `markdown_files/`: Directory containing individual Markdown files
- `scraper.log`: Detailed logging information
- `failed_urls.txt`: List of URLs that failed to download (if any)

## Configuration

You can modify the following constants in the script:

- `MAX_WORKERS`: Number of concurrent downloads (default: 5)
- `MAX_RETRIES`: Number of retry attempts for failed requests (default: 3)
- `TIMEOUT`: Request timeout in seconds (default: 10)
- `OUTPUT_FILE`: Name of the aggregated output file (default: "p2p_aggregated_docs.md")

## Features

- **Concurrent Downloads**: Uses ThreadPoolExecutor for efficient downloading
- **Progress Tracking**: Shows a progress bar for downloads using tqdm (main script) or percentage in terminal (simple script)
- **Robust Error Handling**: Implements retry logic with exponential backoff
- **Rate Limiting**: Controls concurrent requests to avoid overwhelming the server
- **Detailed Logging**: Logs all actions and errors for troubleshooting
- **Table of Contents**: Generates a navigable table of contents in the output file

## License

MIT
