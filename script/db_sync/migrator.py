from pymongo import UpdateOne
from decimal import Decimal
from typing import TypedDict
from datetime import datetime
from dateutil.relativedelta import relativedelta
import config
from connector import MongoDbConnector, SqlConnector
import asyncio
from pymongo import DESCENDING

class PathMapping(TypedDict):
    MongoDb: str
    SQL: str

def rows_to_dicts(cursor, rows):
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

def sanitize_for_mongo(doc):
    def convert_value(value):
        if isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, dict):
            return {k: convert_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [convert_value(v) for v in value]
        else:
            return value

    return {k: convert_value(v) for k, v in doc.items()}

def get_necessary_columns(paths: list[dict]):
    return ", ".join(path["SQL"] for path in paths)

async def migrate_collection(collection_name: str, instructions: dict, mongodb_connector: MongoDbConnector, sql_connector: SqlConnector):
    print(f"Starting migration of collection {collection_name} with instructions {instructions}")

    # await mongo_connector.db["updates"].insert_one({"start_date": start_date, "end_date": end_date, "duration": (end_date - start_date).total_seconds()}) # pyright: ignore[reportOptionalSubscript]

    identifier_field = instructions["IDENTIFIER"]
    await mongodb_connector.db[collection_name].create_index(identifier_field, unique=True) # pyright: ignore[reportOptionalSubscript]

    runtime_variables = {
        "COLUMNS": get_necessary_columns(instructions["PATHS"]),
        "LIMIT_DATE": datetime.today() - relativedelta(years=config.YEAR_LIMIT),
        "LAST_UPDATE": await mongodb_connector.db["updates"].find_one(sort=[("end_date", DESCENDING)]) # pyright: ignore[reportOptionalSubscript]
    }

    if not runtime_variables["LAST_UPDATE"]:
        runtime_variables["LAST_UPDATE"] = datetime.min
    else:
        runtime_variables["LAST_UPDATE"] = runtime_variables["LAST_UPDATE"]["start_date"]

    runtime_variables["LAST_UPDATE"] = datetime.min

    query: str = instructions["SQL_QUERY"].format(columns=runtime_variables["COLUMNS"])

    if "SQL_PARAMS" in instructions.keys():
        collection = sql_connector.cursor.execute(query, (runtime_variables["LIMIT_DATE"], runtime_variables["LAST_UPDATE"])) # pyright: ignore[reportOptionalMemberAccess]
    else:
        collection = sql_connector.cursor.execute(query, (runtime_variables["LAST_UPDATE"])) # pyright: ignore[reportOptionalMemberAccess]

    raw_rows = collection.fetchall()
    docs = rows_to_dicts(sql_connector.cursor, raw_rows)
    print(f"{len(docs)} documents fetched")

    identifier_field = instructions["IDENTIFIER"]
    paths = instructions['PATHS']
    operations = []
    i = 0
    for doc in docs:
        i += 1
        mongo_doc = sanitize_for_mongo({
            path["MongoDb"]: doc[path["SQL"]]
            for path in paths
            if path["SQL"] in doc
        })
        identifier_value = mongo_doc.get(identifier_field)
        if identifier_value is not None:
            filter_doc = {identifier_field: identifier_value}
            update_doc = {"$set": mongo_doc}
            operations.append(
                UpdateOne(
                    filter_doc,
                    update_doc,
                    upsert=True
                )
            )
    if operations:
        await mongodb_connector.db[collection_name].bulk_write(operations) # pyright: ignore[reportOptionalSubscript]

def migrate_sql_to_mongodb():
    with SqlConnector() as sql_connector:
        if not sql_connector.connection:
            print("Failed to connect to SQL database")
            return

        with MongoDbConnector() as mongo_connector:
            if not mongo_connector.client:
                print("Failed to connect to MongoDB database")
                return

            async def run_migrations():
                for collection_name, instructions in config.MIGRATION_CONFIG.items():
                    await migrate_collection(collection_name, instructions, mongo_connector, sql_connector)

            asyncio.run(run_migrations())

    print("All documents inserted in the database")

if __name__ == "__main__":
    migrate_sql_to_mongodb()
