import os
from urllib.parse import quote_plus
from pymongo import MongoClient

MONGO_DB_NAME = os.getenv('AZURE_MONGO_DB')


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


def create_collection(client, collection_name):
    try:
        db = client.get_database(MONGO_DB_NAME)
        if collection_name not in db.list_collection_names():
            mongo_collection = db.create_collection(collection_name)
            print(
                f"Database '{MONGO_DB_NAME}' and Collection '{collection_name}' created successfully.")
            return mongo_collection
        else:
            print(
                f"Collection '{collection_name}' already exists in database '{MONGO_DB_NAME}'.")
            return db.get_collection(collection_name)
    except Exception as e:
        print(
            f"Error creating collection '{collection_name}' in database '{MONGO_DB_NAME}': {e}")
        return None


def insert_file_analysis_data(client, collection_name, file_path, file_hash, summary, repo_url):
    # Construct the document with the required and optional fields
    file_document = {
        'repo_url': repo_url,
        'file_path': file_path,
        'file_hash': file_hash,
        'summary': summary
    }
    print(f"Preparing to insert/update document for file: {file_path}")
    # Use the generic insert_document function to perform the actual DB operation
    db = client.get_database(MONGO_DB_NAME)
    mongo_collection = db.get_collection(collection_name)
    print(mongo_collection)
    query = {'file_path': file_document.get('file_path')}
    try:
        # Use replace_one with upsert=True to insert if not found, or replace if found
        result = mongo_collection.replace_one(
            query, file_document, upsert=True)

        if result.matched_count == 0 and result.upserted_id is not None:
            print(
                f"Document for file '{file_document['file_path']}' inserted with _id: {result.upserted_id}")
        elif result.matched_count > 0:
            print(
                f"Document for file '{file_document['file_path']}' replaced/updated successfully.")
        else:
            print(
                f"Document operation for file '{file_document['file_path']}' status unknown.")

    except Exception as e:
        print(
            f"Error inserting/updating document for file '{file_document.get('file_path', 'N/A')}': {e}")
