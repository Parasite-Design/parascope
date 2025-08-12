import asyncio

import config
from connector import MongoDbConnector


def index_documents():
    with MongoDbConnector() as mongo_connector:
        if not mongo_connector.client:
            print("Failed to connect to MongoDB database")
            return

        async def run_indexer():
            db = mongo_connector.db
            for entry in config.INDEXING_CONFIG:
                collection_name = entry["collection"]
                field = entry["field"]
                unique = bool(entry.get("unique", 0))
                collection = db[collection_name]  # pyright: ignore[reportOptionalSubscript]
                await ensure_index_async(collection, field, unique=unique)
                print(f"Ensured index on {collection_name}.{field} (unique={unique})")

        async def ensure_index_async(collection, index_spec, **options):
            if isinstance(index_spec, str):
                idx_spec = [(index_spec, 1)]
            elif not isinstance(index_spec, list):
                raise ValueError(
                    "index_spec must be a string or a list of (field, direction) tuples"
                )
            else:
                idx_spec = index_spec
            existing_indexes = await collection.index_information()
            for index in existing_indexes.values():
                if set(tuple(pair) for pair in index["key"]) == set(
                    tuple(pair) for pair in idx_spec
                ):
                    if "unique" in options:
                        if index.get("unique", False) != options["unique"]:
                            raise ValueError(
                                f"Index on {idx_spec} already exists with different unique option"
                            )
                    return
            await collection.create_index(idx_spec, **options)

        asyncio.run(run_indexer())
    print("All indexes ensured")
