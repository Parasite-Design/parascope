import asyncio
import config
from migrator import migrate_sql_to_mongodb
from linker import link_documents
from cleanup import cleanup
from datetime import datetime
from index import index_documents

from connector import MongoDbConnector


if __name__ == "__main__":
    start_date = datetime.now()
    # migrate_sql_to_mongodb()
    # cleanup(config=config.MIGRATION_CLEANUP_CONFIG)
    # index_documents()
    # link_documents()
    cleanup(config=config.LINKING_CLEANUP_CONFIG)
    end_date = datetime.now()

    with MongoDbConnector() as mongo_connector:
        if not mongo_connector.client:
            print("Failed to connect to MongoDB database")
            exit(1)

        async def run_migrations():
            await mongo_connector.db["updates"].insert_one({"start_date": start_date, "end_date": end_date, "duration": (end_date - start_date).total_seconds()}) # pyright: ignore[reportOptionalSubscript]

    asyncio.run(run_migrations())

    print("All migrations and linking completed successfully")
