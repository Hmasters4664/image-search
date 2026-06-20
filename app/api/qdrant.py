from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from qdrant_client.http.exceptions import UnexpectedResponse

client = QdrantClient(url="http://127.0.0.1:6333",prefer_grpc=False)


def get_or_create_collection(team_id: str):
    collection_name = f"team_{team_id}"  # e.g. "team_acme", "team_123"

    try:
        client.get_collection(collection_name)
        print(f"Collection {collection_name} already exists")
    except UnexpectedResponse:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=768,
                distance=Distance.COSINE
            )
        )
        print(f"Created collection {collection_name}")

    return collection_name

def index_image(team_id: str, embedding, metadata: dict = {}):
    collection_name = get_or_create_collection(team_id)
    client.upsert(
        collection_name=collection_name,
        points=[PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload=metadata
        )]
    )

def embed_base64_image(image_base64: str):
    image_data = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    inputs = processor(images=[image], return_tensors="pt")

    with torch.no_grad():
        outputs = model.vision_model(**inputs)

    embedding = outputs.last_hidden_state[:, 0, :]  # CLS token
    embedding = torch.nn.functional.normalize(embedding, dim=-1)

    return embedding.squeeze().tolist()