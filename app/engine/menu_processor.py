# flake8: noqa: E402
from dotenv import load_dotenv
load_dotenv()
import os
import json
import logging
import requests
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
from datetime import datetime
from llama_index.core import Document
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core.settings import Settings
from llama_index.core.program import FunctionCallingProgram
from app.settings import init_settings
from app.models.menu import Menu, MenuSection, Dish
import argparse
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MenuProcessor:
    """Class to process restaurant websites and extract menu information."""

    def __init__(self, pdf_storage_dir: str = "data/raw/menus/pdf", 
                 html_storage_dir: str = "data/raw/menus/html"):
        """Initialize the MenuProcessor with storage directories."""
        self.pdf_storage_dir = pdf_storage_dir
        self.html_storage_dir = html_storage_dir
        self.llm = Settings.llm
        self.visited_urls = set()  # Keep track of visited URLs
        os.makedirs(self.pdf_storage_dir, exist_ok=True)
        os.makedirs(self.html_storage_dir, exist_ok=True)
        logger.info(f"PDF storage directory set to: {self.pdf_storage_dir}")
        logger.info(f"HTML storage directory set to: {self.html_storage_dir}")

    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs belong to the same domain."""
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        return domain1 == domain2

    def _is_menu_related(self, url: str) -> bool:
        """Check if a URL is likely menu-related based on keywords."""
        menu_keywords = {
            'cardapio', 'menu', 'carta', 'comida', 'bebida', 'drink',
            'vinho', 'wine', 'cocktail', 'coquetel', 'almoco', 'jantar',
            'entrada', 'prato', 'sobremesa', 'dessert'
        }
        url_lower = url.lower()
        return any(keyword in url_lower for keyword in menu_keywords)

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from the HTML content."""
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Only include links from the same domain
            if self._is_same_domain(base_url, absolute_url):
                links.append(absolute_url)
        
        return list(set(links))  # Remove duplicates

    def _crawl_website(self, base_url: str, restaurant_name: str) -> List[Dict]:
        """Crawl the website to find menu-related pages."""
        menu_pages = []
        to_visit = {base_url}
        
        while to_visit and len(self.visited_urls) < 50:  # Limit crawling depth
            url = to_visit.pop()
            if url in self.visited_urls:
                continue
                
            try:
                logger.info(f"Crawling URL: {url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
                
                response = requests.get(url, headers=headers, timeout=30)
                self.visited_urls.add(url)
                
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # If this page is menu-related, add it to our list
                if self._is_menu_related(url):
                    page_title = soup.title.string if soup.title else url
                    menu_pages.append({
                        "name": f"{restaurant_name} - {page_title}",
                        "url": url,
                        "location": "Sao Paulo"  # You might want to make this configurable
                    })
                
                # Add new links to visit
                new_links = self._extract_links(soup, base_url)
                to_visit.update(link for link in new_links if link not in self.visited_urls)
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {str(e)}")
                continue
        
        return menu_pages

    def process_website(self, url: str, restaurant_name: str) -> Dict:
        """Process a restaurant website to extract menu information."""
        try:
            # First, crawl the website to find all menu-related pages
            menu_pages = self._crawl_website(url, restaurant_name)
            logger.info(f"Found {len(menu_pages)} menu-related pages")
            
            # Process each menu page
            all_menus = []
            for page in menu_pages:
                try:
                    logger.info(f"Processing menu page: {page['url']}")
                    logger.info(f"Fetching URL: {page['url']}")
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-User': '?1',
                        'Sec-Fetch-Dest': 'document',
                        'Cache-Control': 'max-age=0'
                    }
                    
                    response = requests.get(page['url'], headers=headers, timeout=30)
                    logger.info(f"Response status code: {response.status_code}")
                    
                    # Save raw HTML
                    safe_name = "".join(c if c.isalnum() else "_" for c in page['name'])
                    html_path = os.path.join(self.html_storage_dir, f"{safe_name}.html")
                    logger.info(f"Attempting to save HTML to: {html_path}")
                    
                    try:
                        with open(html_path, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        logger.info(f"Successfully saved raw HTML to {html_path}")
                    except Exception as e:
                        logger.error(f"Error saving HTML file: {str(e)}")
                        
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Use FunctionCallingProgram to extract menu data
                    prompt_template_str = """\
                    Extract ALL menu information from this HTML content in a structured format.
                    
                    First, find ALL menu sections by looking for:
                    1. h1 tags with class 'elementor-heading-title' (e.g., 'ENTRADAS', 'PIZZETAS', 'BURGUER', 'SALADAS')
                    2. Each section starts with a heading and contains multiple dishes
                    3. The sections are scattered throughout the page, so look for ALL headings
                    
                    For EACH section found, extract ALL dishes under that section by looking for:
                    1. Dish names in h2 tags with class 'elementor-heading-title'
                    2. Descriptions in div tags with class 'elementor-widget-container' or 'text-tuca'
                    3. Prices are usually in spans near the dish name
                    4. Special notes like wine pairings are in p tags
                    5. Image URLs are in img tags within 'ha-modal-content__image' divs
                    6. Dietary information is shown with icons:
                       - vegetariano.png for vegetarian
                       - semgluten.png for gluten-free
                       - vegano.png for vegan
                       - semlactose.png for lactose-free

                    Important:
                    - Make sure to capture ALL sections, not just the first one
                    - Include ALL dishes under each section
                    - Format prices as strings without currency symbols
                    - The menu is in Brazilian Portuguese (pt-BR) and uses Brazilian Real (BRL)
                    - Look for content in both visible text and HTML attributes
                    - Pay attention to the document structure, as sections may be far apart

                    HTML Content:
                    {html_content}
                    """
                    
                    program = FunctionCallingProgram.from_defaults(
                        output_cls=Menu,
                        prompt_template_str=prompt_template_str,
                        llm=self.llm,
                        verbose=True
                    )

                    menu = program(
                        html_content=response.text,
                        restaurant_name=page['name'],
                        url=page['url'],
                        raw_html_path=html_path,
                        language='pt-BR',
                        currency='BRL'
                    )
                    all_menus.append(menu.model_dump())
                    
                except Exception as e:
                    logger.error(f"Error processing menu page: {str(e)}")
                    continue
            
            return all_menus
            
        except Exception as e:
            logger.error(f"Error processing website: {str(e)}")
            return {
                "error": str(e),
                "restaurant_name": restaurant_name,
                "url": url,
                "extracted_at": datetime.utcnow().isoformat(),
                "raw_html_path": None
            }

    def process_menus(self, restaurant_urls: List[Dict[str, str]]) -> Dict:
        """
        Process menus from a list of restaurant URLs.
        
        Args:
            restaurant_urls: List of dicts containing restaurant info
                           [{"name": "Restaurant Name", "url": "https://..."}]
        
        Returns:
            Dict containing processing results for each restaurant
        """
        results = {}
        
        for restaurant in restaurant_urls:
            try:
                logger.info(f"Processing restaurant: {restaurant['name']}")
                menus = self.process_website(restaurant['url'], restaurant['name'])
                
                if isinstance(menus, list):
                    # If we got multiple menus back, store them all
                    results[restaurant['name']] = {
                        'menus': menus,
                        'base_url': restaurant['url'],
                        'extracted_at': datetime.utcnow().isoformat()
                    }
                else:
                    # If we got a single menu or error, store it directly
                    results[restaurant['name']] = menus
                    
            except Exception as e:
                logger.error(f"Error processing {restaurant['name']}: {str(e)}")
                results[restaurant['name']] = {
                    'error': str(e),
                    'url': restaurant['url']
                }
        
        return results

    def _find_pdf_menus(self, soup: BeautifulSoup) -> List[str]:
        """Find PDF menu links in the HTML."""
        pdf_links = []
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if href.lower().endswith('.pdf') and any(word in href.lower() for word in ['menu', 'carte']):
                pdf_links.append(href)
        return pdf_links
    
    def _save_pdf_menus(self, pdf_links: List[str], restaurant_name: str):
        """Download and save PDF menus."""
        for i, link in enumerate(pdf_links):
            try:
                response = requests.get(link)
                filename = f"{restaurant_name}_menu_{i+1}.pdf"
                filepath = os.path.join(self.pdf_storage_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Saved PDF menu to {filepath}")
            except Exception as e:
                logger.error(f"Error saving PDF from {link}: {str(e)}")
    
    def _extract_menu_from_html(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Use LLM to extract menu information from HTML."""
        # Create a prompt for the LLM to analyze the HTML
        prompt = f"""
        Analyze the following HTML content and extract menu items if present.
        Focus on finding:
        1. Menu sections
        2. Dishes and their descriptions
        3. Prices
        4. Any special notes or dietary information

        HTML content:
        {soup.text[:4000]}  # Limit content length
        
        Return the menu information in a structured format if found, or None if no menu is present.
        """
        
        response = self.llm.complete(prompt)
        # Process and structure the LLM's response
        try:
            # Try to parse the response as structured data
            menu_data = json.loads(response.text)
            return menu_data
        except json.JSONDecodeError:
            # If not JSON, return the raw text
            return {"raw_text": response.text} if response.text.strip() else None

def process_menus(restaurant_urls: List[Dict[str, str]]) -> Dict:
    """
    Process menus from a list of restaurant URLs.
    
    Args:
        restaurant_urls: List of dicts containing restaurant info
                       [{"name": "Restaurant Name", "url": "https://..."}]
    
    Returns:
        Dict containing processing results for each restaurant
    """
    processor = MenuProcessor()
    results = {}
    
    for restaurant in restaurant_urls:
        logger.info(f"Processing menu for {restaurant['name']}")
        result = processor.process_website(restaurant['url'], restaurant['name'])
        results[restaurant['name']] = {
            **restaurant,  # Include original restaurant data
            **result      # Add the processing results
        }
    
    return results

def datetime_handler(obj):
    """Handle datetime serialization for JSON dumps."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

def main():
    """Main function to run the menu extraction."""
    parser = argparse.ArgumentParser(description='Extract menus from restaurant websites')
    parser.add_argument('--input', type=str, required=True, help='Path to input JSON file with restaurant data')
    parser.add_argument('--output', type=str, default='data/extracted_menus.json', help='Path to output JSON file')
    args = parser.parse_args()

    # Initialize settings
    init_settings()
    
    # Load restaurant data
    with open(args.input, 'r') as f:
        data = json.load(f)
        restaurants = data.get('restaurants', [])
    
    # Process each restaurant
    results = []
    processor = MenuProcessor()
    
    for restaurant in restaurants:
        print(f"\n=== {restaurant['name']} ===")
        result = processor.process_website(restaurant['url'], restaurant['name'])
        
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print("Successfully extracted menu")
            print(json.dumps(result, indent=2, ensure_ascii=False, default=datetime_handler))
        
        results.append(result)
    
    # Save results
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=datetime_handler)
    
    logger.info(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
