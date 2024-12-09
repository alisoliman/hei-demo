from typing import Dict, List, Optional, Union, Literal, Any
import logging
import requests
from enum import Enum
from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field
from datetime import datetime, time
from zoneinfo import ZoneInfo

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

class VenueSearchResult(BaseModel):
    """Data model for venue search results."""
    id: int = Field(..., description="Internal venue ID")
    outlet_name: str = Field(..., description="Name of the venue")
    tripadvisor_id: Optional[str] = Field(None, description="TripAdvisor ID of the venue")
    street: Optional[str] = Field(None, description="Street name")
    street_no: Optional[str] = Field(None, description="Street number")
    district: Optional[str] = Field(None, description="District/neighborhood")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    g_rating: Optional[float] = Field(None, description="Google rating")
    g_user_ratings_total: Optional[int] = Field(None, description="Total number of Google ratings")

class OccasionSuggestion(BaseModel):
    """Data model for occasion suggestions."""
    occasion: str = Field(..., description="Type of occasion suggested")
    confidence: float = Field(..., description="Confidence score for the suggestion")
    reasons: List[str] = Field(..., description="List of reasons for the suggestion")

class OccasionSuggestionResponse(BaseModel):
    """Response model for occasion suggestions."""
    venue_id: int = Field(..., description="Internal venue ID")
    venue_name: str = Field(..., description="Name of the venue")
    suggestions: List[OccasionSuggestion] = Field(..., description="List of occasion suggestions")

class ReservationRequest(BaseModel):
    """Data model for making a reservation request."""
    reservation_time: str = Field(..., description="Time of the reservation")
    number_of_people: int = Field(..., description="Number of people in the reservation")
    dietary_requirements: Optional[str] = Field(None, description="Any dietary requirements or notes")

class ReservationResponse(BaseModel):
    """Data model for reservation response."""
    id: int = Field(..., description="Reservation ID")
    venue_id: str = Field(..., description="TripAdvisor ID of the venue")
    reservation_time: datetime = Field(..., description="Time of the reservation")
    number_of_people: int = Field(..., description="Number of people in the reservation")
    dietary_requirements: Optional[str] = Field(None, description="Dietary requirements or notes")
    status: str = Field(..., description="Status of the reservation (confirmed, cancelled, etc.)")
    created_at: datetime = Field(..., description="When the reservation was created")
    updated_at: datetime = Field(..., description="When the reservation was last updated")

class ChinchinAPITool:
    """Tool for interacting with the Chinchin API."""
    
    # Class variable for base URL
    BASE_URL = "http://localhost:8001/api/v1"
    
    def __init__(self):
        """Initialize the Chinchin API tool."""
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
                    logger.error(f"Invalid occasion type: {occasion_type}")
                    return []

            response = requests.get(
                f"{self.BASE_URL}/venues/search/by-occasion/{occasion_type.value}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching venues by occasion: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching venues by occasion: {str(e)}")
            return []

    def search_venues_by_name(self, name: str) -> List[VenueSearchResult]:
        """
        Search for venues by name.
        
        Args:
            name (str): Name of the venue to search for
            
        Returns:
            List[VenueSearchResult]: List of venues matching the search query.
            Returns empty list if any error occurs.
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/venues/search/by-name/",
                params={"name": name},
                headers=self.headers
            )
            response.raise_for_status()
            
            venues = []
            for venue_data in response.json():
                try:
                    venue = VenueSearchResult(
                        id=venue_data["id"],
                        outlet_name=venue_data["outlet_name"],
                        tripadvisor_id=venue_data.get("tripadvisor_id"),
                        street=venue_data.get("street"),
                        street_no=venue_data.get("street_no"),
                        district=venue_data.get("district"),
                        city=venue_data.get("city"),
                        state=venue_data.get("state"),
                        g_rating=venue_data.get("g_rating"),
                        g_user_ratings_total=venue_data.get("g_user_ratings_total")
                    )
                    venues.append(venue)
                except Exception as e:
                    logger.error(f"Error processing venue data: {str(e)}")
                    continue
            
            return venues
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching venues by name: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching venues by name: {str(e)}")
            return []

    def get_occasion_suggestions(self, tripadvisor_id: str) -> List[Dict[str, Union[str, float, List[str]]]]:
        """
        Get suggested occasions for a specific venue.
        
        Args:
            tripadvisor_id (str): TripAdvisor ID of the venue
            
        Returns:
            List[Dict[str, Union[str, float, List[str]]]]: List of suggested occasions with confidence scores and reasons
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/venues/{tripadvisor_id}/occasion-suggestions",
                headers=self.headers
            )
            response.raise_for_status()
            
            # Parse the response into our model
            suggestion_data = OccasionSuggestionResponse(**response.json())
            
            # Return a list of suggestions in a more usable format
            return [
                {
                    "occasion": suggestion.occasion,
                    "confidence": suggestion.confidence,
                    "reasons": suggestion.reasons
                }
                for suggestion in suggestion_data.suggestions
            ]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting occasion suggestions: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting occasion suggestions: {str(e)}")
            return []

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
                f"{self.BASE_URL}/menu-items/venue/{tripadvisor_id}",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting venue menu: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting venue menu: {str(e)}")
            return []

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
                f"{self.BASE_URL}/menu-items/search/",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching menu items: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching menu items: {str(e)}")
            return []

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
                f"{self.BASE_URL}/menu-items/stats/{tripadvisor_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting menu stats: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting menu stats: {str(e)}")
            return {}

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
                f"{self.BASE_URL}/menu-items/categories/{tripadvisor_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting price aggregations: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting price aggregations: {str(e)}")
            return {}

    @staticmethod
    def get_venue_reservations(
        tripadvisor_id: str,
        status: Optional[str] = None,
        from_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all reservations for a venue.
        
        Args:
            tripadvisor_id (str): TripAdvisor ID of the venue
            status (str, optional): Filter by status ("confirmed" or "cancelled")
            from_date (str, optional): Get reservations from this date onwards (ISO format)
            
        Returns:
            List[Dict[str, Any]]: List of reservations
        """
        url = f"{ChinchinAPITool.BASE_URL}/venues/venue/{tripadvisor_id}/reservations"
        params = {}
        
        if status:
            params['status'] = status
        if from_date:
            params['from_date'] = from_date
            
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get venue reservations: {str(e)}")
            return []

    @staticmethod
    def make_reservation(
        tripadvisor_id: str,
        time: str,
        num_people: int,
        dietary_requirements: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make a reservation at a venue.
        
        Args:
            tripadvisor_id (str): TripAdvisor ID of the venue
            time (str): Natural language time expression (e.g., "next Friday at 6:30 PM")
            num_people (int): Number of people in the reservation
            dietary_requirements (str, optional): Any dietary requirements or notes
            
        Returns:
            Dict containing the reservation details and confirmation status
        """
        url = f"{ChinchinAPITool.BASE_URL}/venues/{tripadvisor_id}/reserve"
        
        # Format the request according to the ReservationRequest model
        data = {
            "reservation_time": time,
            "number_of_people": num_people
        }
        if dietary_requirements:
            data["dietary_requirements"] = dietary_requirements
        
        headers = {
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {str(e)}")
            if response := getattr(e, 'response', None):
                try:
                    error_json = response.json()
                    error_detail = error_json.get('detail', str(e))
                    if "does not accept reservations" in str(error_detail):
                        return {"error": f"The venue with TripAdvisor ID {tripadvisor_id} does not accept reservations. Please choose a different venue or contact the venue directly."}
                    return {"error": error_detail}
                except:
                    return {"error": str(e)}
            return {"error": str(e)}

    @staticmethod
    def make_reservation_wrapper(
        tripadvisor_id: str,
        time: str,
        num_people: int,
        dietary_requirements: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make a reservation at a venue.
        
        Args:
            tripadvisor_id (str): TripAdvisor ID of the venue
            time (str): Natural language time expression (e.g., "next Friday at 6:30 PM")
            num_people (int): Number of people in the reservation
            dietary_requirements (str, optional): Any dietary requirements or notes
            
        Returns:
            Dict containing the reservation details and confirmation status
        """
        try:
            response = ChinchinAPITool.make_reservation(
                tripadvisor_id,
                time,
                num_people,
                dietary_requirements
            )
            if "error" in response:
                raise ValueError(f"Reservation failed: {response['error']}")
            return response
        except Exception as e:
            logging.error(f"Error making reservation: {str(e)}")
            raise

    @staticmethod
    def update_reservation(
        reservation_id: int,
        number_of_people: Optional[int] = None,
        dietary_requirements: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing reservation.
        
        Args:
            reservation_id (int): ID of the reservation to update
            number_of_people (int, optional): New number of people
            dietary_requirements (str, optional): New dietary requirements
            
        Returns:
            Optional[Dict[str, Any]]: Updated reservation if successful, None if failed
        """
        url = f"{ChinchinAPITool.BASE_URL}/venues/reservation/{reservation_id}"
        
        update_data = {}
        if number_of_people is not None:
            update_data["number_of_people"] = number_of_people
        if dietary_requirements is not None:
            update_data["dietary_requirements"] = dietary_requirements
            
        headers = {
            "Content-Type": "application/json",
            "accept": "application/json"
        }
            
        try:
            response = requests.patch(url, json=update_data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to update reservation: {str(e)}")
            if response := getattr(e, 'response', None):
                try:
                    error_detail = response.json().get('detail', str(e))
                    return {"error": error_detail}
                except:
                    return {"error": str(e)}
            return {"error": str(e)}

    @staticmethod
    def update_reservation_wrapper(
        reservation_id: int,
        number_of_people: Optional[int] = None,
        dietary_requirements: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing reservation.
        
        Args:
            reservation_id (int): ID of the reservation to update
            number_of_people (int, optional): New number of people
            dietary_requirements (str, optional): New dietary requirements
            
        Returns:
            Optional[Dict[str, Any]]: Updated reservation if successful, None if failed
        """
        try:
            response = ChinchinAPITool.update_reservation(
                reservation_id,
                number_of_people,
                dietary_requirements
            )
            if "error" in response:
                raise ValueError(f"Update failed: {response['error']}")
            return response
        except Exception as e:
            logging.error(f"Error updating reservation: {str(e)}")
            raise

    @staticmethod
    def cancel_reservation(reservation_id: int) -> bool:
        """Cancel a reservation.
        
        Args:
            reservation_id (int): ID of the reservation to cancel
            
        Returns:
            bool: True if cancelled successfully, False otherwise
        """
        url = f"{ChinchinAPITool.BASE_URL}/venues/reservation/{reservation_id}"
        
        try:
            response = requests.delete(url)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to cancel reservation: {str(e)}")
            return False

    @staticmethod
    def cancel_reservation_wrapper(reservation_id: int) -> bool:
        """Cancel a reservation.
        
        Args:
            reservation_id (int): ID of the reservation to cancel
            
        Returns:
            bool: True if cancelled successfully, False otherwise
        """
        try:
            return ChinchinAPITool.cancel_reservation(reservation_id)
        except Exception as e:
            logging.error(f"Error cancelling reservation: {str(e)}")
            return False


def get_tools():
    """Get the Chinchin API tools."""
    api_tool = ChinchinAPITool()
    
    def search_venues_by_occasion_wrapper(occasion_type: str) -> List[Dict]:
        """Wrapper function to handle string input for occasion type."""
        return api_tool.search_venues_by_occasion(occasion_type)

    @staticmethod
    def make_reservation_wrapper(
        tripadvisor_id: str,
        time: str,
        num_people: int,
        dietary_requirements: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make a reservation at a venue.
        
        Args:
            tripadvisor_id (str): TripAdvisor ID of the venue
            time (str): Natural language time expression (e.g., "next Friday at 6:30 PM")
            num_people (int): Number of people in the reservation
            dietary_requirements (str, optional): Any dietary requirements or notes
            
        Returns:
            Dict containing the reservation details and confirmation status
            
        Examples:
        - make_reservation("123456", "tomorrow at 7:00 PM", 4)
        - make_reservation("123456", "next Friday at 6:30 PM", 2, "2 vegetarians")"""
        try:
            response = ChinchinAPITool.make_reservation(
                tripadvisor_id,
                time,
                num_people,
                dietary_requirements
            )
            if "error" in response:
                raise ValueError(f"Reservation failed: {response['error']}")
            return response
        except Exception as e:
            logging.error(f"Error making reservation: {str(e)}")
            raise

    @staticmethod
    def get_venue_reservations_wrapper(
        tripadvisor_id: str,
        status: Optional[str] = None,
        from_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all reservations for a venue.
        
        Args:
            tripadvisor_id (str): TripAdvisor ID of the venue
            status (str, optional): Filter by status ("confirmed" or "cancelled")
            from_date (str, optional): Get reservations from this date onwards (ISO format)
            
        Returns:
            List[Dict[str, Any]]: List of reservations for the venue"""
        try:
            return ChinchinAPITool.get_venue_reservations(tripadvisor_id, status, from_date)
        except Exception as e:
            logging.error(f"Error getting venue reservations: {str(e)}")
            return []

    def update_reservation_wrapper(
        reservation_id: int,
        number_of_people: Optional[int] = None,
        dietary_requirements: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing reservation.
        
        Args:
            reservation_id (int): ID of the reservation to update
            number_of_people (int, optional): New number of people
            dietary_requirements (str, optional): New dietary requirements
            
        Returns:
            Optional[Dict[str, Any]]: Updated reservation if successful, None if failed"""
        try:
            return ChinchinAPITool.update_reservation(
                reservation_id,
                number_of_people,
                dietary_requirements
            )
        except Exception as e:
            logger.error(f"Error updating reservation: {str(e)}")
            return None

    def cancel_reservation_wrapper(self, reservation_id: int) -> bool:
        """
        Cancel a reservation.
        
        Args:
            reservation_id (int): ID of the reservation to cancel
            
        Returns True if cancelled successfully, False otherwise."""
        try:
            return ChinchinAPITool.cancel_reservation(reservation_id)
        except Exception as e:
            logger.error(f"Error cancelling reservation: {str(e)}")
            return False

    return [
        FunctionTool.from_defaults(
            fn=search_venues_by_occasion_wrapper,
            name="search_venues_by_occasion",
            description="""Search for venues based on specific event types.
            Use this only when you need to find venues for a specific type of occasion.
            For finding a specific venue by name, use search_venues_by_name instead.

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
            fn=api_tool.search_venues_by_name,
            name="search_venues_by_name",
            description="""Primary tool for finding venues by name. Always use this tool first when you need to:
            1. Make a reservation at a specific venue
            2. Find a venue's TripAdvisor ID
            3. Get details about a specific venue
            
            Args:
                name (str): Name of the venue to search for
                
            Returns a list of venues with their details including:
            - TripAdvisor ID (required for reservations)
            - Address information
            - Google ratings
            - And other venue details
            
            Example:
            To make a reservation:
            1. First use this tool to find the venue and get its TripAdvisor ID
            2. Then use make_reservation with the obtained TripAdvisor ID"""
        ),
        FunctionTool.from_defaults(
            fn=api_tool.get_occasion_suggestions,
            name="get_occasion_suggestions",
            description="""Get suggested occasions for a specific venue.
            
            Args:
                tripadvisor_id (str): TripAdvisor ID of the venue
                
            Returns a list of suggested occasions with confidence scores and reasons."""
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
        ),
        FunctionTool.from_defaults(
            fn=make_reservation_wrapper,
            name="make_reservation",
            description="""Make a reservation at a venue.
            
            Args:
                tripadvisor_id (str): TripAdvisor ID of the venue
                time (str): Natural language time expression (e.g., "next Friday at 6:30 PM")
                num_people (int): Number of people in the reservation
                dietary_requirements (str, optional): Any dietary requirements or notes
                
            Returns:
                Dict containing the reservation details and confirmation status
                
            Examples:
            - make_reservation("123456", "tomorrow at 7:00 PM", 4)
            - make_reservation("123456", "next Friday at 6:30 PM", 2, "2 vegetarians")"""
        ),
        FunctionTool.from_defaults(
            fn=get_venue_reservations_wrapper,
            name="get_venue_reservations",
            description="""Get all reservations for a venue.
            
            Args:
                tripadvisor_id (str): TripAdvisor ID of the venue
                status (str, optional): Filter by status ("confirmed" or "cancelled")
                from_date (str, optional): Get reservations from this date onwards (ISO format)
                
            Returns a list of reservations for the venue."""
        ),
        FunctionTool.from_defaults(
            fn=update_reservation_wrapper,
            name="update_reservation",
            description="""Update an existing reservation.
            
            Args:
                reservation_id (int): ID of the reservation to update
                number_of_people (int, optional): New number of people
                dietary_requirements (str, optional): New dietary requirements
                
            Returns:
                Dict containing the updated reservation details if successful"""
        ),
        FunctionTool.from_defaults(
            fn=ChinchinAPITool.cancel_reservation_wrapper,
            name="cancel_reservation",
            description="""Cancel a reservation.
            
            Args:
                reservation_id (int): ID of the reservation to cancel
                
            Returns:
                bool: True if cancelled successfully, False otherwise"""
        ),
    ]
