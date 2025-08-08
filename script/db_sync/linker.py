import asyncio
import config
from connector import MongoDbConnector
import json
from jinja2 import Template


def load_template(path: str, context: dict) -> list:
    try:
        with open(path, encoding='utf-8') as f:
            raw = f.read()
        rendered = Template(raw).render(context)
        return json.loads(rendered)
    except Exception as e:
        print(f"Error rendering template or loading JSON: {e}")
        return []

def link_documents():
    allowed_collections = {"invoices", "models", "products", "customers"}  # Example: define allowed collections
    with MongoDbConnector() as mongo_connector:
        if not mongo_connector.client:
            print("Failed to connect to MongoDB database")
            return

        async def run_linker():
            for link in config.LINKING_CONFIG:
                print(f"Linking documents from {link['remote_collection']} to {link['output_collection']}...")
                output_collection = link.get("output_collection")
                if not output_collection or output_collection not in allowed_collections:
                    print(f"Invalid or unauthorized output_collection: {output_collection}")
                    continue
                try:
                    pipeline = load_template(config.LINKING_TEMPLATE_PATH, link) # pyright: ignore[reportArgumentType]
                    await mongo_connector.db[output_collection].aggregate(pipeline).to_list(length=None) # pyright: ignore[reportOptionalSubscript]
                except Exception as e:
                    print(f"Error during aggregation for {output_collection}: {e}")

        asyncio.run(run_linker())

    print("All documents linked")


if __name__ == "__main__":
    link_documents()
