import requests
import yaml


def read_file_from_repo(repo_url: str, file_path: str, branch: str):
    base_raw_url = repo_url.replace(
        'https://github.com/', 'https://raw.githubusercontent.com/')
    raw_file_url = f"{base_raw_url}/{branch}/{file_path}"

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


def get_files_to_analyse(repo_url: str, file_path: str, branch: str):
    try:
        yaml_content = read_file_from_repo(repo_url, file_path, branch)
        yaml_data = yaml.safe_load(yaml_content)
        if not yaml_data:
            raise ValueError("YAML file is empty or not properly formatted.")
        print(f"Files to analyse: {yaml_data}")
        return yaml_data
    except yaml.YAMLError as yaml_err:
        raise yaml.YAMLError(f"Error parsing YAML content: {yaml_err}")
    except Exception as e:
        print(f"Error fetching YAML file: {e}")


def analyse_files(AZURE_OAI_DEPLOYMENT, openai_client, repo_url: str, file_path: str, branch: str):
    read_files = get_files_to_analyse(repo_url, file_path, branch)
    for file in read_files:
        print(f"File to analyse: {file}")
        code = read_file_from_repo(repo_url, file, branch)
        print(f"Code in {file}: {code[:100]}...")
        # analyse_code(AZURE_OAI_DEPLOYMENT, openai_client, code)
        return analyse_code(AZURE_OAI_DEPLOYMENT, openai_client, code)


def analyse_code(AZURE_OAI_DEPLOYMENT, openai_client, code: str):
    system_role = open(file="system_role.txt",
                       encoding="utf8").read().strip()
    print(f"System role loaded: {system_role}")
    # TODO: set this as a parameter somewhere
    user_message = f"Describe the function of the following Python code:\n\n```python\n{code}\n```.  formatted as an HTML paragraph using the name of the file as a header."
    print("Sending request to Azure OpenAI...")
    response = openai_client.chat.completions.create(
        model=AZURE_OAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_role},
            {"role": "user", "content": user_message}
        ],
        # Controls creativity. Lower for more deterministic output.
        temperature=0.7,
        max_tokens=250,  # Maximum number of tokens in the response
    )
    print("Response received from Azure OpenAI:")
    print(response.choices[0].message.content.strip())
    return response.choices[0].message.content.strip()
