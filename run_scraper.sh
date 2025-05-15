#!/bin/bash

show_help() {
    echo "Usage: ./run_scraper.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help      Show this help message and exit"
    echo "  -s, --simple    Use the simple version (no tqdm dependency)"
    echo "  -m, --minimal   Use minimal dependencies (no tqdm)"
    echo ""
}

# Default values
USE_SIMPLE=false
USE_MINIMAL=false

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            show_help
            exit 0
            ;;
        -s|--simple)
            USE_SIMPLE=true
            shift
            ;;
        -m|--minimal)
            USE_MINIMAL=true
            shift
            ;;
        *)
            echo "Unknown option: $key"
            show_help
            exit 1
            ;;
    esac
done

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
if [ "$USE_MINIMAL" = true ]; then
    pip install -r requirements-minimal.txt
else
    pip install -r requirements.txt
fi

# Run the scraper
echo "Running P2P documentation scraper..."
if [ "$USE_SIMPLE" = true ]; then
    python scrape_p2p_docs_simple.py
else
    python scrape_p2p_docs.py
fi

# Deactivate virtual environment
deactivate

echo "Done! Check p2p_aggregated_docs.md for the aggregated documentation." 