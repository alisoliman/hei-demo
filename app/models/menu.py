from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Dish(BaseModel):
    """A dish on the menu."""
    name: str = Field(..., description="The name of the dish")
    description: str = Field(..., description="Description of the dish")
    price: str = Field(..., description="Price of the dish in the local currency")
    special_notes: Optional[str] = Field(None, description="Any special notes, like wine pairings or dietary restrictions")
    image_url: Optional[str] = Field(None, description="URL to an image of the dish, if available")
    dietary_info: Optional[List[str]] = Field(default_factory=list, description="List of dietary information (vegetarian, vegan, gluten-free, etc.)")


class MenuSection(BaseModel):
    """A section of the menu (e.g., Appetizers, Main Course, etc.)."""
    section_name: str = Field(..., description="Name of the menu section")
    description: Optional[str] = Field(None, description="Description of the section, if any")
    dishes: List[Dish] = Field(..., description="List of dishes in this section")


class Menu(BaseModel):
    """The complete menu for a restaurant."""
    restaurant_name: str = Field(..., description="Name of the restaurant")
    url: str = Field(..., description="URL where the menu was found")
    extracted_at: datetime = Field(default_factory=datetime.now, description="When the menu was extracted")
    language: str = Field(..., description="Language of the menu")
    currency: str = Field(..., description="Currency used in the menu")
    sections: List[MenuSection] = Field(..., description="List of menu sections")
    raw_html_path: Optional[str] = Field(None, description="Path to the saved raw HTML file")
    special_features: Optional[List[str]] = Field(default_factory=list, description="Special features like 'Happy Hour', 'Tasting Menu', etc.")
