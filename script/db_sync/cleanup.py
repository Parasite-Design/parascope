import asyncio

from connector import MongoDbConnector


def cleanup(config):
    with MongoDbConnector() as mongo_connector:
        if not mongo_connector.client:
            print("Failed to connect to MongoDB database")
            return

        async def run_aggregations():
            for agg_def in config:
                collection_name = agg_def.get("collection")
                pipeline = agg_def.get("aggregation")
                if not collection_name or not pipeline:
                    print(f"Invalid aggregation definition: {agg_def}")
                    continue
                print(f"Running aggregation on collection '{collection_name}'...")
                try:
                    await (
                        mongo_connector.db[collection_name]
                        .aggregate(pipeline)
                        .to_list(length=None)
                    )  # pyright: ignore[reportOptionalSubscript]
                    print(f"Aggregation on '{collection_name}' completed.")
                except Exception as e:
                    print(f"Error during aggregation for '{collection_name}': {e}")

        asyncio.run(run_aggregations())

    print("All migration aggregations executed.")
