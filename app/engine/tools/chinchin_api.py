from typing import Dict, List, Optional, Union
import logging
import requests
from enum import Enum
from llama_index.core.tools import FunctionTool

logger = logging.getLogger(__name__)

class OccasionType(str, Enum):
    SPECIAL_OCCASION = "Special Occasion"
    DINNER_OUT = "Dinner Out"
    DATE_NIGHT = "Date Night / Romantic"
    CHILLED_DRINK = "Chilled Drink"
    QUICK_BEER = "Quick Beer"
    AFTER_WORK = "After Work"
    FAMILY_GET_TOGETHER = "Family get together"
    GIRLS_NIGHT = "Girls Night"
    BIG_NIGHT_OUT = "Big Night Out"
    LARGE_GROUPS = "Large Groups"
    BRUNCH = "Brunch"
    FOOTBALL_GET_TOGETHER = "Football Get-Together"

class ChinchinAPITool:
    def __init__(self):
        self.base_url = "http://localhost:8001/api/v1"
        self.headers = {
            "accept": "application/json"
        }

    def search_venues_by_occasion(self, occasion_type: Union[str, OccasionType]) -> List[Dict]:
        """
        Search for venues based on specific occasion types.
        
        Args:
            occasion_type (Union[str, OccasionType]): Type of occasion to search for. Must be one of:
                - SPECIAL_OCCASION: "Special Occasion"
                - DINNER_OUT: "Dinner Out"
                - DATE_NIGHT: "Date Night / Romantic"
                - CHILLED_DRINK: "Chilled Drink"
                - QUICK_BEER: "Quick Beer"
                - AFTER_WORK: "After Work"
                - FAMILY_GET_TOGETHER: "Family get together"
                - GIRLS_NIGHT: "Girls Night"
                - BIG_NIGHT_OUT: "Big Night Out"
                - LARGE_GROUPS: "Large Groups"
                - BRUNCH: "Brunch"
                - FOOTBALL_GET_TOGETHER: "Football Get-Together"
            
        Returns:
            List[Dict]: List of venues matching the occasion type
        """
        try:
            # Convert string input to enum if needed
            if isinstance(occasion_type, str):
                try:
                    # Try to find the enum by value first
                    occasion_enum = next(
                        (enum_type for enum_type in OccasionType if enum_type.value == occasion_type),
                        None
                    )
                    if occasion_enum is None:
                        # If not found by value, try to find by name
                        occasion_enum = OccasionType[occasion_type]
                    occasion_type = occasion_enum
                except (KeyError, StopIteration):
                    raise ValueError(
                        f"Invalid occasion type: {occasion_type}. Must be one of: "
                        + ", ".join(f"{e.name}: '{e.value}'" for e in OccasionType)
                    )

            response = requests.get(
                f"{self.base_url}/venues/search/by-occasion/{occasion_type.value}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error searching venues by occasion: {str(e)}")
            raise

    def get_occasion_suggestions(self, tripadvisor_id: str) -> List[OccasionType]:
        """
        Get suggested occasions for a specific venue.
        
        Args:
            tripadvisor_id (str): TripAdvisor ID of the venue
            
        Returns:
            List[OccasionType]: List of suggested occasions from the OccasionType enum
        """
        try:
            response = requests.get(
                f"{self.base_url}/venues/{tripadvisor_id}/occasion-suggestions",
                headers=self.headers
            )
            response.raise_for_status()
            return [OccasionType(occasion) for occasion in response.json()]
        except Exception as e:
            logger.error(f"Error getting occasion suggestions: {str(e)}")
            raise

    def get_venue_menu(self, tripadvisor_id: str, category: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Dict]:
        """
        Get menu items for a specific venue.
        
        Args:
            tripadvisor_id (str): TripAdvisor ID of the venue
            category (str, optional): Filter by category
            skip (int): Number of items to skip (default: 0)
            limit (int): Maximum number of items to return (default: 100)
            
        Returns:
            List[Dict]: List of menu items for the venue
        """
        try:
            params = {
                "category": category,
                "skip": skip,
                "limit": limit
            }
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            response = requests.get(
                f"{self.base_url}/menu-items/venue/{tripadvisor_id}",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting venue menu: {str(e)}")
            raise

    def search_menu_items(
        self,
        query: Optional[str] = None,
        tripadvisor_id: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search menu items with various filters.
        
        Args:
            query (str, optional): Text search in title and description
            tripadvisor_id (str, optional): Filter by venue's TripAdvisor ID
            category (str, optional): Filter by category
            min_price (float, optional): Minimum price
            max_price (float, optional): Maximum price
            tags (List[str], optional): Filter by tags
            skip (int): Number of items to skip (default: 0)
            limit (int): Maximum number of items to return (default: 100)
            
        Returns:
            List[Dict]: List of menu items matching the criteria
        """
        try:
            params = {
                "query": query,
                "tripadvisor_id": tripadvisor_id,
                "category": category,
                "min_price": min_price,
                "max_price": max_price,
                "tags": tags,
                "skip": skip,
                "limit": limit
            }
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            response = requests.get(
                f"{self.base_url}/menu-items/search/",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error searching menu items: {str(e)}")
            raise

    def get_menu_stats(self, tripadvisor_id: str) -> Dict:
        """
        Get statistical information about a venue's menu.
        
        Args:
            tripadvisor_id (str): TripAdvisor ID of the venue
            
        Returns:
            Dict: Menu statistics including:
                - Total number of items
                - Number of items per category
                - Price ranges
                - Most common tags
        """
        try:
            response = requests.get(
                f"{self.base_url}/menu-items/stats/{tripadvisor_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting menu stats: {str(e)}")
            raise

    def get_price_aggregations(self, tripadvisor_id: str) -> Dict:
        """
        Get price aggregations per category for a venue.
        
        Args:
            tripadvisor_id (str): TripAdvisor ID of the venue
            
        Returns:
            Dict: Price aggregations per category:
                {
                    "category1": {
                        "min_price": X,
                        "max_price": Y,
                        "avg_price": Z
                    }
                }
        """
        try:
            response = requests.get(
                f"{self.base_url}/menu-items/categories/{tripadvisor_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting price aggregations: {str(e)}")
            raise

def get_tools():
    """Get the Chinchin API tools."""
    api_tool = ChinchinAPITool()
    
    def search_venues_by_occasion_wrapper(occasion_type: str) -> List[Dict]:
        """Wrapper function to handle string input for occasion type."""
        return api_tool.search_venues_by_occasion(occasion_type)

    return [
        FunctionTool.from_defaults(
            fn=search_venues_by_occasion_wrapper,
            name="search_venues_by_occasion",
            description="""Search for venues based on specific occasion types.
            
            Args:
                occasion_type (str): Must be one of:
                    - "Special Occasion"
                    - "Dinner Out"
                    - "Date Night / Romantic"
                    - "Chilled Drink"
                    - "Quick Beer"
                    - "After Work"
                    - "Family get together"
                    - "Girls Night"
                    - "Big Night Out"
                    - "Large Groups"
                    - "Brunch"
                    - "Football Get-Together"
            """
        ),
        FunctionTool.from_defaults(
            fn=api_tool.get_occasion_suggestions,
            name="get_occasion_suggestions",
            description="""Get suggested occasions for a specific venue.
            
            Args:
                tripadvisor_id (str): TripAdvisor ID of the venue
                
            Returns a list of suggested occasions from the OccasionType enum."""
        ),
        FunctionTool.from_defaults(
            fn=api_tool.get_venue_menu,
            name="get_venue_menu",
            description="""Get menu items for a specific venue.
            
            Args:
                tripadvisor_id (str): TripAdvisor ID of the venue
                category (str, optional): Filter by category
                skip (int): Number of items to skip (default: 0)
                limit (int): Maximum number of items to return (default: 100)
                
            Returns a list of menu items for the venue."""
        ),
        FunctionTool.from_defaults(
            fn=api_tool.search_menu_items,
            name="search_menu_items",
            description="""Search menu items with various filters.
            
            Args:
                query (str, optional): Text search in title and description
                tripadvisor_id (str, optional): Filter by venue's TripAdvisor ID
                category (str, optional): Filter by category
                min_price (float, optional): Minimum price
                max_price (float, optional): Maximum price
                tags (List[str], optional): Filter by tags
                skip (int): Number of items to skip (default: 0)
                limit (int): Maximum number of items to return (default: 100)
                
            Returns a list of menu items matching the criteria."""
        ),
        FunctionTool.from_defaults(
            fn=api_tool.get_menu_stats,
            name="get_menu_stats",
            description="""Get statistical information about a venue's menu.
            
            Args:
                tripadvisor_id (str): TripAdvisor ID of the venue
                
            Returns menu statistics including:
                - Total number of items
                - Number of items per category
                - Price ranges
                - Most common tags"""
        ),
        FunctionTool.from_defaults(
            fn=api_tool.get_price_aggregations,
            name="get_price_aggregations",
            description="""Get price aggregations per category for a venue.
            
            Args:
                tripadvisor_id (str): TripAdvisor ID of the venue
                
            Returns price aggregations per category:
                {
                    "category1": {
                        "min_price": X,
                        "max_price": Y,
                        "avg_price": Z
                    }
                }"""
        )
    ]
