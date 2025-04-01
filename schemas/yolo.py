from pydantic import BaseModel
from typing import Set

class ImageAnalysisResponse(BaseModel):
    """
    Response model for image analysis.

    example:
    {
        "id": 1,
        "labels": [
            "person"
        ]
    }
    """
    id: int
    labels: Set[str]