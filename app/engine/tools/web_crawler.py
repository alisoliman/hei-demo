import requests
from bs4 import BeautifulSoup
from typing import Dict, Any

class RestaurantInfo:
    def __init__(self, name: str, address: str, phone: str, website: str):
        self.name = name
        self.address = address
        self.phone = phone
        self.website = website

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "address": self.address,
            "phone": self.phone,
            "website": self.website,
        }

def crawl_restaurant(url: str) -> RestaurantInfo:
    """
    Crawl a restaurant website to extract basic information.

    Args:
        url (str): The URL of the restaurant website.

    Returns:
        RestaurantInfo: An object containing the restaurant's information.
    """
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    # Example parsing logic (this will vary based on actual website structure)
    name = soup.find("h1", class_="restaurant-name").get_text(strip=True)
    address = soup.find("p", class_="restaurant-address").get_text(strip=True)
    phone = soup.find("span", class_="restaurant-phone").get_text(strip=True)
    website = url

    return RestaurantInfo(name=name, address=address, phone=phone, website=website)

def get_tools() -> list:
    """Return the web crawler tool."""
    return [
        {
            "name": "crawl_restaurant",
            "function": crawl_restaurant,
            "description": "Crawl a restaurant website to extract basic information."
        }
    ]
