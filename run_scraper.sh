#!/bin/bash

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
pip install -r requirements.txt

# Run the scraper
echo "Running P2P documentation aggregator..."
python scrape_p2p_docs.py

# Deactivate virtual environment
deactivate

echo "Done! Check p2p_aggregated_docs.md for the aggregated documentation." 