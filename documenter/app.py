import os
import sys
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from openai import AzureOpenAI
from controllers import analyse_files

app = Flask(__name__)

# Initializing the core application


def init_app():
    app = Flask(__name__)
    load_dotenv()
    app.config.from_pyfile('settings.cfg', silent=True)

    # Load global configurations
    AZURE_OAI_KEY = os.getenv('AZURE_OAI_KEY')
    if not AZURE_OAI_KEY:
        raise ValueError(
            "AZURE_OAI_KEY is not set in the environment variables or settings.cfg file.")

    AZURE_OAI_ENDPOINT = app.config.get('AZURE_OAI_ENDPOINT')
    if not AZURE_OAI_ENDPOINT:
        raise ValueError(
            "AZURE_OAI_ENDPOINT is not set in the settings.cfg file.")

    AZURE_OAI_DEPLOYMENT = app.config.get('AZURE_OAI_DEPLOYMENT')
    if not AZURE_OAI_DEPLOYMENT:
        raise ValueError(
            "AZURE_OAI_DEPLOYMENT is not set in the settings.cfg file.")

    AZURE_OAI_API_VERSION = app.config.get('AZURE_OAI_API_VERSION')
    if not AZURE_OAI_API_VERSION:
        raise ValueError(
            "AZURE_OAI_API_VERSION is not set in the settings.cfg file.")

    # --- Initialize AzureOpenAI Client (Best Practice: Global or App Context) ---
    try:
        openai_client = AzureOpenAI(
            azure_endpoint=AZURE_OAI_ENDPOINT,
            api_key=AZURE_OAI_KEY,
            api_version=app.config['AZURE_OAI_API_VERSION'],
            timeout=20.0  # Set a global timeout for all OpenAI calls
        )
    except Exception as e:
        print(f"Failed to initialize AzureOpenAI client: {e}", file=sys.stderr)
        sys.exit(1)

    @app.route("/")
    def home():
        return f"Hackathon Documenter is running! <br> " \
            f"Azure OpenAI Endpoint: {AZURE_OAI_ENDPOINT} <br> "\
            f"Azure OpenAI Deployment: {AZURE_OAI_DEPLOYMENT} <br> "\
            f"Azure OpenAI API Version: {AZURE_OAI_API_VERSION} <br> "

    @app.route("/analyse", methods=['POST'])
    def analyse():
        """
        Receives an URL of a project to analyse.
        """
        data = request.get_json()
        repo_url = data.get('repoUrl')
        branch = data.get('branch', 'main')
        file_path = data.get('filePath', 'documenter.yaml')
        if not repo_url:
            return "URL is required for analysis.", 400
        print(
            f"Received repo URL: {repo_url}, branch: {branch}, file path: {file_path}")
        data = analyse_files(AZURE_OAI_DEPLOYMENT,
                             openai_client, repo_url, file_path, branch)
        return data

    @app.route("/generate-summary", methods=['POST'])
    def generate_summary():
        # Placeholder for summary generation logic
        return "Summary generation endpoint is under construction."

    return app


app = init_app()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
