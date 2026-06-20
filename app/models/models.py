from fastapi import FastAPI
from pydantic import BaseModel


class ImageInput(BaseModel):
    appwrite_id: str  # Appwrite ID for the image
    backblaze_id: str  # Backblaze ID for the image
    team_id: str  # Team ID for the image
    file_name: str  # File name of the image

class ImageSearchRequest(BaseModel):
    image: str  # Base64 encoded image string
    team_id: str  # Team ID for the image