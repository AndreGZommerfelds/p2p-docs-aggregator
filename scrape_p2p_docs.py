import requests
import re
import time
import random
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

# Try to import tqdm, and handle the case when it's not installed
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("WARNING: tqdm package not found. This package is required for the progress bar.")
    print("You can install it with: pip install tqdm")
    print("Alternatively, use the simple version: python scrape_p2p_docs_simple.py")
    print("Continue without tqdm? (y/n)")
    if input().lower() != 'y':
        sys.exit(1)
    print("Continuing without progress bar...")

# Constants
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
BASE_URL = "https://docs.p2p.org/"
INITIAL_URL = "https://docs.p2p.org/llms.txt"
OUTPUT_FILE = "p2p_aggregated_docs.md"
MAX_WORKERS = 5
MAX_RETRIES = 3
TIMEOUT = 10
RETRY_DELAY_BASE = 2  # base seconds for exponential backoff

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def fetch_url(url, retries=MAX_RETRIES, timeout=TIMEOUT):
    """
    Fetch content from a URL with retry logic and error handling.
    
    Args:
        url (str): The URL to fetch
        retries (int): Number of retry attempts
        timeout (int): Request timeout in seconds
        
    Returns:
        str or None: The text content if successful, None otherwise
    """
    headers = {"User-Agent": USER_AGENT}
    
    for attempt in range(retries + 1):
        try:
            logger.debug(f"Fetching {url} (Attempt {attempt + 1}/{retries + 1})")
            response = requests.get(url, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                logger.warning(f"Resource not found (404): {url}")
                return None  # Don't retry for 404s
            else:
                logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
                
        except requests.Timeout:
            logger.warning(f"Timeout error fetching {url}")
        except requests.ConnectionError:
            logger.warning(f"Connection error fetching {url}")
        except requests.RequestException as e:
            logger.warning(f"Error fetching {url}: {e}")
            
        if attempt < retries:
            # Exponential backoff with jitter
            delay = RETRY_DELAY_BASE ** attempt + random.uniform(0, 1)
            logger.info(f"Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
    
    logger.error(f"Failed to fetch {url} after {retries + 1} attempts")
    return None

def extract_md_links(text_content):
    """
    Extract all markdown links from text content.
    
    Args:
        text_content (str): The text content to search for markdown links
        
    Returns:
        set: A set of unique markdown file URLs
    """
    if not text_content:
        return set()
    
    # Pattern to match markdown links: [text](url.md)
    # This will find both relative and absolute URLs ending with .md
    pattern = r'\[.*?\]\((.*?\.md)\)'
    matches = re.findall(pattern, text_content)
    
    # Convert relative URLs to absolute URLs
    absolute_urls = set()
    for match in matches:
        if match.startswith(('http://', 'https://')):
            absolute_urls.add(match)
        else:
            absolute_urls.add(urljoin(BASE_URL, match))
    
    logger.info(f"Found {len(absolute_urls)} unique markdown links")
    return absolute_urls

def download_md_file(url):
    """
    Download a markdown file from a URL.
    
    Args:
        url (str): The URL of the markdown file
        
    Returns:
        tuple: (url, content) where content is the file content or None if failed
    """
    content = fetch_url(url)
    
    if content:
        return url, content
    else:
        return url, None

def main():
    """Main function to orchestrate the scraping process."""
    start_time = time.time()
    logger.info("Starting P2P documentation scraping")
    
    # Step 1: Fetch the initial text file
    logger.info(f"Fetching main file: {INITIAL_URL}")
    main_content = fetch_url(INITIAL_URL)
    
    if not main_content:
        logger.error("Failed to fetch the main file. Exiting.")
        return
    
    # Step 2: Extract markdown links
    md_links = extract_md_links(main_content)
    logger.info(f"Found {len(md_links)} unique markdown links to download")
    
    if not md_links:
        logger.warning("No markdown links found. Exiting.")
        return
    
    # Step 3: Download markdown files concurrently
    logger.info(f"Downloading {len(md_links)} markdown files using {MAX_WORKERS} workers")
    results = []
    failed_urls = []
    
    # Create a directory to store individual markdown files (optional)
    md_files_dir = "markdown_files"
    if not os.path.exists(md_files_dir):
        os.makedirs(md_files_dir)
    
    # Use ThreadPoolExecutor with progress bar
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all download tasks
        future_to_url = {executor.submit(download_md_file, url): url for url in md_links}
        
        # Process results as they complete with a progress bar
        if TQDM_AVAILABLE:
            # Use tqdm if available
            with tqdm(total=len(md_links), desc="Downloading files", unit="file") as progress_bar:
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        url, content = future.result()
                        if content:
                            results.append((url, content))
                            
                            # Save individual markdown file (optional)
                            filename = os.path.basename(url)
                            filepath = os.path.join(md_files_dir, filename)
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(content)
                        else:
                            failed_urls.append(url)
                            logger.error(f"Failed to download: {url}")
                    except Exception as exc:
                        failed_urls.append(url)
                        logger.error(f"An error occurred with {url}: {exc}")
                    finally:
                        progress_bar.update(1)
        else:
            # Fallback to simple progress tracking if tqdm is not available
            total = len(md_links)
            completed = 0
            
            print(f"Downloading {total} files:")
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                completed += 1
                
                # Print progress percentage
                progress = (completed / total) * 100
                print(f"Progress: {progress:.1f}% ({completed}/{total})", end='\r')
                
                try:
                    url, content = future.result()
                    if content:
                        results.append((url, content))
                        
                        # Save individual markdown file
                        filename = os.path.basename(url)
                        filepath = os.path.join(md_files_dir, filename)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                    else:
                        failed_urls.append(url)
                        logger.error(f"Failed to download: {url}")
                except Exception as exc:
                    failed_urls.append(url)
                    logger.error(f"An error occurred with {url}: {exc}")
            
            print()  # New line after progress indicator
    
    success_count = len(results)
    failure_count = len(failed_urls)
    
    logger.info(f"Successfully downloaded {success_count} out of {len(md_links)} files")
    if failure_count > 0:
        logger.warning(f"Failed to download {failure_count} files")
    
    # Step 4: Aggregate content into a single markdown file
    logger.info(f"Aggregating content into {OUTPUT_FILE}")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# P2P.org Aggregated Documentation\n\n")
        f.write(f"*This file contains aggregated documentation from {success_count} markdown files.*\n\n")
        f.write(f"*Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        
        # Add table of contents
        f.write("## Table of Contents\n\n")
        for i, (url, _) in enumerate(results, 1):
            filename = os.path.basename(url)
            title = filename.replace('.md', '').replace('-', ' ').title()
            f.write(f"{i}. [{title}](#{title.lower().replace(' ', '-')})\n")
        
        f.write("\n---\n\n")
        
        # Add content of each file
        for url, content in results:
            filename = os.path.basename(url)
            title = filename.replace('.md', '').replace('-', ' ').title()
            
            f.write(f"## {title}\n\n")
            f.write(f"*Source: [{url}]({url})*\n\n")
            f.write(content)
            f.write("\n\n---\n\n")
    
    # Write failed URLs to a separate file if any
    if failed_urls:
        with open("failed_urls.txt", 'w', encoding='utf-8') as f:
            for url in failed_urls:
                f.write(f"{url}\n")
        logger.info(f"List of failed URLs saved to failed_urls.txt")
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"Aggregation complete. Output saved to {OUTPUT_FILE}")
    logger.info(f"Total files processed: {success_count}/{len(md_links)} ({failure_count} failed)")
    logger.info(f"Total execution time: {duration:.2f} seconds")
    
    print(f"\nDone! Output saved to {OUTPUT_FILE}")
    print(f"Successfully processed {success_count} out of {len(md_links)} files in {duration:.2f} seconds")
    if failure_count > 0:
        print(f"Failed to download {failure_count} files. See failed_urls.txt for details.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        print("\nProcess interrupted by user. Exiting...")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        print(f"\nAn unexpected error occurred: {e}") 