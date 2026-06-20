import base64
import io
from uuid import uuid4

import torch
from b2sdk.v1 import B2Api, InMemoryAccountInfo
from fastapi import APIRouter
from PIL import Image
from qdrant_client.models import PointStruct
from transformers import AutoModel, AutoProcessor

from app.api.qdrant import client as qdrant_client
from app.api.qdrant import get_or_create_collection
from app.models.models import ImageInput, ImageSearchRequest
from app.settings import settings

router = APIRouter()

model_id = "google/siglip2-base-patch16-224"
model = AutoModel.from_pretrained(model_id).eval()
processor = AutoProcessor.from_pretrained(model_id)

def _require(value: str, name: str) -> str:
    if not value:
        raise RuntimeError(f"Missing required setting: {name}")
    return value


def _create_bucket():
    b2_api = B2Api(InMemoryAccountInfo())
    b2_api.authorize_account(
        "production",
        _require(settings.b2_key_id, "B2_KEY_ID"),
        _require(settings.b2_app_key, "B2_APP_KEY"),
    )
    return b2_api.get_bucket_by_id(_require(settings.b2_bucket_id, "B2_BUCKET_ID"))


bucket = _create_bucket()


def _embed_image(image: Image.Image) -> list[float]:
    inputs = processor(images=[image], return_tensors="pt")

    with torch.no_grad():
        outputs = model.vision_model(**inputs)

    embedding = outputs.last_hidden_state[:, 0, :]
    embedding = torch.nn.functional.normalize(embedding, dim=-1)
    return embedding.squeeze().tolist()


def _download_image(backblaze_id: str) -> Image.Image:
    downloaded_file = bucket.download_file_by_id(backblaze_id)
    image_buffer = io.BytesIO()
    downloaded_file.save(image_buffer)
    image_buffer.seek(0)
    return Image.open(image_buffer).convert("RGB")

@router.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}

@router.post("/embed", tags=["embed"])
def embed_image(image_input: ImageInput) -> dict[str, list[float]]:
    image = _download_image(image_input.backblaze_id)
    embedding = _embed_image(image)

    collection_name = get_or_create_collection(image_input.team_id)
    qdrant_client.upsert(
        collection_name=collection_name,
        points=[
            PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload={
                    "appwrite_id": image_input.appwrite_id,
                    "backblaze_id": image_input.backblaze_id,
                    "file_name": image_input.file_name,
                },
            )
        ],
    )

    return {"embedding": embedding}

@router.post("/image-search", tags=["search"])
def search_with_image(image_input: ImageSearchRequest):
    image_data = base64.b64decode(image_input.image)
    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    embedding = _embed_image(image)
    collection_name = get_or_create_collection(image_input.team_id)
    results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=embedding,
        limit=10,
        with_payload=True,
    )
    return {"results": [result.model_dump() for result in results]}