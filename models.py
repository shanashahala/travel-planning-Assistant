# models.py

from typing import Optional, List
from pydantic import BaseModel, Field


class ExtractedPreferences(BaseModel):
    """Structured output for extracted user preferences"""
    package_type: Optional[str] = Field(
        None,
        description="Type: beach, hills, heritage, honeymoon, adventure, pilgrimage"
    )
    destination: Optional[str] = Field(
        None,
        description="Specific destination (e.g., Goa, Manali)"
    )
    budget: Optional[float] = Field(
        None,
        description="Budget in numerical format"
    )
    duration_days: Optional[int] = Field(
        None,
        description="Trip duration in days"
    )
    traveler_type: Optional[str] = Field(
        None,
        description="Type: solo, couple, family_2, family_3, family_4, family_5, group"
    )
    activities: List[str] = Field(
        default_factory=list,
        description="List of activities user wants to do (e.g., ['scuba diving', 'sightseeing'])"
    )
    confidence: str = Field(
        description="Confidence: high, medium, low"
    )
    notes: Optional[str] = Field(
        None,
        description="Extraction notes or ambiguities"
    )