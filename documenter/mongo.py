import os
from urllib.parse import quote_plus
from pymongo import MongoClient


def get_mongo_client():

    MONGO_USERNAME = os.getenv('AZURE_MONGO_USER')
    MONGO_PASSWORD = os.getenv('AZURE_MONGO_PASSWORD')
    MONGO_HOST = os.getenv('AZURE_MONGO_HOST')

    encoded_password = quote_plus(MONGO_PASSWORD)
    mongo_uri = f"mongodb+srv://{MONGO_USERNAME}:{encoded_password}@{MONGO_HOST}"
    print(f"Connecting to MongoDB at {mongo_uri}")
    client = MongoClient(mongo_uri)
    return client


def insert_document(client, collection, document):
    MONGO_DB_NAME = os.getenv('AZURE_MONGO_DB')
    print(MONGO_DB_NAME)
    print(collection)
    db = client.get_database(MONGO_DB_NAME)
    print(db)
    mongo_collection = db.get_collection(collection)
    print(mongo_collection)

    try:
        result = mongo_collection.replace_one(
            {'_id': document['_id']}, document, upsert=True)
    except Exception as e:
        print(f"Error inserting document: {e}")


def find_document(client, collection, document_id):
    MONGO_DB_NAME = os.getenv('AZURE_MONGO_DB')
    db = client.get_database(MONGO_DB_NAME)
    mongo_collection = db.get_collection(collection)

    try:
        document = mongo_collection.find_one({'_id': document_id})
        print(document)
        return document
    except Exception as e:
        print(f"Error finding document: {e}")
        return None


def close_client(client):
    try:
        client.close()
        print("MongoDB client connection closed.")
    except Exception as e:
        print(f"Error closing MongoDB client: {e}")
