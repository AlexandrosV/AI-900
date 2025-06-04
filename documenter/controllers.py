import datetime
import requests
import hashlib
import yaml
import mongo
import os


def generate_github_raw_url(repo_url: str, file_path: str, branch: str):
    base_raw_url = repo_url.replace(
        'https://github.com/', 'https://raw.githubusercontent.com/')
    raw_file_url = f"{base_raw_url}/{branch}/{file_path}"
    return raw_file_url


def read_file_from_repo(raw_file_url: str):
    print(f"Attempting to read YAML from: {raw_file_url}")
    try:
        response = requests.get(raw_file_url)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.text
        print(f"Content retrieved successfully: {raw_file_url}")
        return data
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 404:
            raise ValueError(
                f"File not found at URL: {raw_file_url}. Check repo URL, file path, and branch. Error: {http_err}")
        else:
            raise requests.exceptions.RequestException(
                f"HTTP error occurred: {http_err} - Status: {response.status_code}")
    except requests.exceptions.ConnectionError as conn_err:
        raise requests.exceptions.RequestException(
            f"Connection error occurred: {conn_err}. Check internet connection or URL.")
    except requests.exceptions.Timeout as timeout_err:
        raise requests.exceptions.RequestException(
            f"The request timed out: {timeout_err}. Server might be slow or network unstable.")
    except requests.exceptions.RequestException as req_err:
        raise requests.exceptions.RequestException(
            f"An unexpected request error occurred: {req_err}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")


def get_files_to_analyse(raw_file_url):
    try:
        yaml_content = read_file_from_repo(raw_file_url)
        yaml_data = yaml.safe_load(yaml_content)
        if not yaml_data:
            raise ValueError("YAML file is empty or not properly formatted.")
        print(f"Files to analyse: {yaml_data}")
        return yaml_data
    except yaml.YAMLError as yaml_err:
        raise yaml.YAMLError(f"Error parsing YAML content: {yaml_err}")
    except Exception as e:
        print(f"Error fetching YAML file: {e}")


def generate_sha256_hash(code: str):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(code.encode('utf-8'))
    return sha256_hash.hexdigest()


def analyse_files(AZURE_OAI_DEPLOYMENT, openai_client, repo_url: str, file_path: str, branch: str):
    raw_file_url = generate_github_raw_url(repo_url, file_path, branch)
    read_files = get_files_to_analyse(raw_file_url)
    document = {'_id': repo_url, 'id': repo_url, 'mainFiles': [], 'projectSummary': '',
                'documentationURL': '', 'updatedAt': datetime.datetime.now()}
    COLLECTION = os.getenv('AZURE_MONGO_COLLECTION')
    mongo_client = mongo.get_mongo_client()
    print(mongo_client)
    mongo.create_collection(mongo_client, COLLECTION)
    for file in read_files:
        temp_raw = generate_github_raw_url(repo_url, file, branch)
        print(f"File to analyse: {file}")
        code = read_file_from_repo(temp_raw)
        hash = generate_sha256_hash(code)
        language = get_code_language(AZURE_OAI_DEPLOYMENT, openai_client, code)
        summary = analyse_code(AZURE_OAI_DEPLOYMENT,
                               openai_client, code, language)
        mainFile = {'path': temp_raw, 'hash': hash, 'summary': summary}
        mongo.insert_file_analysis_data(
            mongo_client, COLLECTION, temp_raw, hash, summary, repo_url)
        document['mainFiles'].append(mainFile)
        print(summary)
    ######
    # mongo.insert_document(mongo_client, COLLECTION, document)
    # mongo.find_document(mongo_client, COLLECTION, repo_url)
    mongo.close_client(mongo_client)
    return "All Done!"


def replace_word_simple(text: str, old_word: str, new_word: str):
    return text.replace(old_word, new_word)


def get_code_language(AZURE_OAI_DEPLOYMENT, openai_client, code: str):
    system_role = 'You are an AI programming copilot that helps developers.'
    print(f"System role loaded: {system_role}")
    user_message = f"Identify the programming language of the following code:\n\n```\n{code}\n```. Give your answer in one word"
    print("Sending request to Azure OpenAI...")
    response = openai_client.chat.completions.create(
        model=AZURE_OAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": user_message}
        ],
        # Controls creativity. Lower for more deterministic output.
        temperature=0.7,
        max_tokens=1000,  # Maximum number of tokens in the response
    )
    print("Response received from Azure OpenAI:")
    print(response.choices[0].message.content.strip())
    return response.choices[0].message.content.strip()


def analyse_code(AZURE_OAI_DEPLOYMENT, openai_client, code: str, language: str):
    system_role = open(file="system_role.txt",
                       encoding="utf8").read().strip()
    system_role = replace_word_simple(system_role, "LANGUAGE", language)
    print(f"System role loaded: {system_role}")
    # TODO: set this as a parameter somewhere
    # user_message = f"Describe the function of the following Python code:\n\n```{language}\n{code}\n```, formatted as an HTML paragraph using the name of the file as a header."
    user_message = f"Describe the function of the following Python code:\n\n```python\n{code}\n```."
    print("Sending request to Azure OpenAI...")
    response = openai_client.chat.completions.create(
        model=AZURE_OAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": user_message}
        ],
        # Controls creativity. Lower for more deterministic output.
        temperature=0.7,
        max_tokens=1000,  # Maximum number of tokens in the response
    )
    print("Response received from Azure OpenAI:")
    print(response.choices[0].message.content.strip())
    return response.choices[0].message.content.strip()
