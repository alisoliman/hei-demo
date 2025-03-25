from typing import Dict, List, Optional
import os
import requests
import logging
from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

logger = logging.getLogger(__name__)

class ReviewData(BaseModel):
    """Data model for a TripAdvisor review."""
    rating: int = Field(..., description="Rating given in the review")
    title: str = Field(..., description="Title of the review")
    text: str = Field(..., description="Text content of the review")
    published_date: str = Field(..., description="Date when review was published")
    username: str = Field(..., description="Username of the reviewer")
    language: str = Field(..., description="Language of the review")

class TripAdvisorResponse(BaseModel):
    """Response model for TripAdvisor data."""
    location_id: str = Field(..., description="TripAdvisor location ID")
    reviews: List[ReviewData] = Field(..., description="List of reviews")
    average_rating: Optional[float] = Field(None, description="Average rating from reviews")
    total_reviews: Optional[int] = Field(None, description="Total number of reviews")

def get_tripadvisor_reviews(location_id: str, limit: int = 5) -> TripAdvisorResponse:
    """
    Fetch reviews for a specific location from TripAdvisor.
    
    Args:
        location_id (str): The TripAdvisor location ID (must be a numeric ID between 5-10 digits)
        limit (int): Number of reviews to retrieve (default: 5)
        
    Returns:
        TripAdvisorResponse: Structured response containing reviews and metadata.
        Returns empty response if any error occurs.
    """
    try:
        # Validate that location_id looks like a TripAdvisor ID
        if not location_id.isdigit():
            logger.error(
                f"Invalid TripAdvisor ID format. Expected a numeric ID, got: '{location_id}'. "
                "You must first use the search_venues_by_name tool to get the correct TripAdvisor ID."
            )
            return TripAdvisorResponse(
                location_id=location_id,
                reviews=[],
                average_rating=0.0,
                total_reviews=0
            )
        
        # Additional validation for length (TripAdvisor IDs are typically 5-10 digits)
        if len(location_id) < 5 or len(location_id) > 10:
            logger.error(
                f"Invalid TripAdvisor ID length. Expected 5-10 digits, got: {len(location_id)} digits. "
                "This doesn't look like a valid TripAdvisor ID. "
                "Street numbers and other numeric values are not valid TripAdvisor IDs."
            )
            return TripAdvisorResponse(
                location_id=location_id,
                reviews=[],
                average_rating=0.0,
                total_reviews=0
            )

        api_key = os.getenv("TRIPADVISOR_API_KEY")
        if not api_key:
            logger.error("TRIPADVISOR_API_KEY environment variable is not set")
            return TripAdvisorResponse(
                location_id=location_id,
                reviews=[],
                average_rating=0.0,
                total_reviews=0
            )

        url = f"https://api.content.tripadvisor.com/api/v1/location/{location_id}/reviews"
        params = {
            'key': api_key,
            'limit': limit,
            'language': 'pt'
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        reviews_data = data.get('data', [])
        
        # Process reviews into our data model
        reviews = []
        total_rating = 0
        
        for review in reviews_data:
            try:
                review_data = ReviewData(
                    rating=review.get('rating', 0),
                    title=review.get('title', ''),
                    text=review.get('text', ''),
                    published_date=review.get('published_date', ''),
                    username=review.get('user', {}).get('username', 'Anonymous'),
                    language=review.get('language', 'en')
                )
                reviews.append(review_data)
                total_rating += review_data.rating
            except Exception as e:
                logger.error(f"Error processing review data: {str(e)}")
                continue
        
        # Calculate average rating
        average_rating = total_rating / len(reviews) if reviews else 0
        
        return TripAdvisorResponse(
            location_id=location_id,
            reviews=reviews,
            average_rating=round(average_rating, 1),
            total_reviews=len(reviews)
        )
        
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 401:
                error_msg = "Invalid TripAdvisor API key. Please check your API key."
            elif e.response.status_code == 404:
                error_msg = f"Location ID {location_id} not found on TripAdvisor."
            elif e.response.status_code == 429:
                error_msg = "Rate limit exceeded. Please try again later."
        
        logger.error(f"Error fetching TripAdvisor reviews: {error_msg}")
        return TripAdvisorResponse(
            location_id=location_id,
            reviews=[],
            average_rating=0.0,
            total_reviews=0
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching TripAdvisor reviews: {str(e)}")
        return TripAdvisorResponse(
            location_id=location_id,
            reviews=[],
            average_rating=0.0,
            total_reviews=0
        )

def format_reviews_markdown(response: TripAdvisorResponse) -> str:
    """Format TripAdvisor reviews as markdown for display."""
    sections = []
    
    # Add header with rating
    if response.average_rating is not None:
        stars = "⭐" * round(response.average_rating)
        sections.append(f"### TripAdvisor Reviews {stars}\n")
        sections.append(f"Average Rating: {response.average_rating}/5")
        if response.total_reviews is not None:
            sections.append(f"Total Reviews: {response.total_reviews}\n")
    
    # Add individual reviews
    for review in response.reviews:
        stars = "⭐" * review.rating
        sections.append(f"#### {review.title} {stars}")
        sections.append(f"*by {review.username} on {review.published_date}*\n")
        sections.append(f"{review.text}\n")
    
    return "\n".join(sections)

def get_tools():
    """Get the TripAdvisor tools."""
    return [
        FunctionTool.from_defaults(
            fn=get_tripadvisor_reviews,
            name="get_tripadvisor_reviews",
            description="""Get TripAdvisor reviews for a venue.
            
            IMPORTANT: Do NOT use this tool directly with a venue name!
            1. FIRST use the search_venues_by_name tool to get the venue's TripAdvisor ID
            2. ONLY use the numeric TripAdvisor ID returned by search_venues_by_name
            
            Args:
                tripadvisor_id (str): The numeric TripAdvisor ID for the venue
                
            Examples:
            WRONG: get_tripadvisor_reviews("Vista Jardins")
            RIGHT: First use search_venues_by_name to get ID, then get_tripadvisor_reviews("123456")"""
        )
    ]
