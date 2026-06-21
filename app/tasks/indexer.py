import asyncio
from appwrite.client import Client
from appwrite.services.tables_db import TablesDB
from appwrite.query import Query

from app.settings import settings
from app.api.qdrant import get_or_create_collection, client as qdrant_client
# reuse the helpers already in routes.py — consider moving them to a shared module
from app.api.routes import _download_image, _embed_image, bucket

from qdrant_client.models import PointStruct
from uuid import uuid4


def _get_appwrite_db():
    client = Client()
    client.set_endpoint(settings.appwrite_endpoint)
    client.set_project(settings.appwrite_project_id)
    client.set_key(settings.appwrite_api_key)
    return TablesDB(client)


async def sync_unindexed_images():
    """Pull unindexed images from Appwrite and index them into Qdrant."""
    db = _get_appwrite_db()

    # Query documents not yet indexed — assumes you have an `indexed` boolean field
    response = db.list_rows(
        database_id=settings.appwrite_database_id,
        table_id=settings.appwrite_collection_id,
        queries=[Query.or_queries([Query.equal("imageIndexer", False), Query.is_null("imageIndexer")]), Query.equal("type", "image")],
    )

    rows = response.rows
    print(f"Found {len(rows)} unindexed images")

    for row in rows:
        try:
            image = await asyncio.to_thread(_download_image, row.data["b2FileId"])
            embedding = await asyncio.to_thread(_embed_image, image)

            collection_name = get_or_create_collection(row.data["teamId"])
            qdrant_client.upsert(
                collection_name=collection_name,
                points=[PointStruct(
                    id=str(uuid4()),
                    vector=embedding,
                    payload={
                        "appwrite_id": row.id,
                        "backblaze_id": row.data["b2FileId"],
                        "file_name": row.data.get("file_name", ""),
                    },
                )],
            )

            # Mark as indexed in Appwrite
            db.update_row(
                database_id=settings.appwrite_database_id,
                table_id=settings.appwrite_collection_id,
                row_id=row.id,
                data={"imageIndexer": True},
            )
            print(f"Indexed {row.id}")

        except Exception as e:
            print(f"Failed to index {row.id}: {e}")


async def indexer_loop(interval_seconds: int = 60):
    while True:
        try:
            await sync_unindexed_images()
        except Exception as e:
            print(f"Indexer error: {e}")
        await asyncio.sleep(interval_seconds)