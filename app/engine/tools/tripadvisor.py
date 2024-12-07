import os
import requests
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

class ReviewData(BaseModel):
    """Data model for a TripAdvisor review."""
    rating: int = Field(..., description="Rating given by the reviewer (1-5)")
    title: str = Field(..., description="Title of the review")
    text: str = Field(..., description="Full text of the review")
    published_date: str = Field(..., description="Date when the review was published")
    username: str = Field(..., description="Name of the reviewer")
    language: str = Field(..., description="Language of the review")

class TripAdvisorResponse(BaseModel):
    """Response from TripAdvisor API."""
    location_id: str = Field(..., description="TripAdvisor location ID")
    reviews: List[ReviewData] = Field(..., description="List of reviews")
    average_rating: Optional[float] = Field(None, description="Average rating from reviews")
    total_reviews: Optional[int] = Field(None, description="Total number of reviews")

def get_tripadvisor_reviews(location_id: str, limit: int = 5) -> TripAdvisorResponse:
    """
    Fetch reviews for a specific location from TripAdvisor.
    
    Args:
        location_id (str): The TripAdvisor location ID
        limit (int): Number of reviews to retrieve (default: 5)
        
    Returns:
        TripAdvisorResponse: Structured response containing reviews and metadata
    """
    api_key = os.getenv("TRIPADVISOR_API_KEY")
    if not api_key:
        raise ValueError("TRIPADVISOR_API_KEY environment variable is not set")

    url = f"https://api.content.tripadvisor.com/api/v1/location/{location_id}/reviews"
    params = {
        'key': api_key,
        'limit': limit,
        'language': 'en'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        reviews_data = data.get('data', [])
        
        # Process reviews into our data model
        reviews = []
        total_rating = 0
        
        for review in reviews_data:
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
        
        # Calculate average rating
        average_rating = total_rating / len(reviews) if reviews else 0
        
        return TripAdvisorResponse(
            location_id=location_id,
            reviews=reviews,
            average_rating=round(average_rating, 1),
            total_reviews=len(reviews)
        )
        
    except requests.RequestException as e:
        error_msg = str(e)
        if response.status_code == 401:
            error_msg = "Invalid TripAdvisor API key. Please check your API key."
        elif response.status_code == 404:
            error_msg = f"Location ID {location_id} not found on TripAdvisor."
        elif response.status_code == 429:
            error_msg = "Rate limit exceeded. Please try again later."
            
        raise Exception(f"Error fetching TripAdvisor reviews: {error_msg}")

def format_reviews_markdown(response: TripAdvisorResponse) -> str:
    """Format TripAdvisor reviews as markdown for display."""
    sections = []
    
    # Add header with average rating
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

def get_tools(**kwargs) -> List[FunctionTool]:
    """Get the TripAdvisor tools."""
    return [
        FunctionTool.from_defaults(
            fn=get_tripadvisor_reviews,
            name="get_tripadvisor_reviews",
            description="""Use this tool to fetch and analyze TripAdvisor reviews for a specific venue.
            The tool will return:
            - Latest reviews with ratings and comments
            - Average rating
            - Total number of reviews retrieved
            
            Only use this tool when you need to provide information about customer reviews and ratings from TripAdvisor.
            You must provide a valid TripAdvisor location ID."""
        )
    ]
