""""""

import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

SLACK_RELAY_ENDPOINT = os.environ.get("SLACK_RELAY_ENDPOINT")
GITHUB_REPO = os.environ.get("GITHUB_REPO")
PORT = int(os.environ.get("PORT"))

NO_SUCH_ENDPOINT = {"error": 'No such endpoint'}
SUCCESS = {"success": 'Slack message sent!'}
SLACK_UNREACHABLE = {"error": 'Slack unreachable.'}
MALFORMED_REQUEST = {"error": 'Malformed request.'}

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER")
GITHUB_REPO_NAME = os.environ.get("GITHUB_REPO_NAME")

OPENPROJECT_API_KEY = os.environ.get("OPENPROJECT_API_KEY")
OPENPROJECT_URL = os.environ.get("OPENPROJECT_URL")

LLM_API_KEY = os.environ.get("LLM_API_KEY")

SURREALDB_NS = os.environ.get("SURREALDB_NS", "relayops")
SURREALDB_DB = os.environ.get("SURREALDB_DB", "data")

SURREALDB_USER = os.environ.get("SURREALDB_USER", "root")
SURREALDB_PASS = os.environ.get("SURREALDB_PASS", "root")

SURREALDB_HOST = os.environ.get("SURREALDB_HOST", "localhost")
SURREALDB_PORT = os.environ.get("SURREALDB_PORT", 8011)

OP_PORT = 8130

PROJECT_IDS_DICT = {
    'Scrum project': 2
}

USERS_LOOKUP_TABLE = {
    'Darren MacKenzie': 5
}

PRIORITIES = {
    'Normal': 8,
    'High': 9,
    # etc...
}


class Priority:
    def __init__(self, id: int, name: str, position: int, color: str, is_default: bool = False, is_active: bool = True):
        self.id = id
        self.name = name
        self.position = position
        self.color = color
        self.is_default = is_default
        self.is_active = is_active

    #def __str__(self): return f"Priority: {self.name} (ID: {self.id})"
    def __str__(self): return f"/api/v3/priorities/{self.id}"

    def d(self):
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "color": self.color,
            "isDefault": self.is_default,
            "isActive": self.is_active
        }

Normal = Priority(8, 'Normal', 2, '#74C0FC', is_default=True)
Low = Priority(7, 'Low', 1, '#C5F6FA')
High = Priority(9, 'High', 3, '#F59F00')


OP_JSON_OUTPUT_PATH = 'output/op/'
JIRA_JSON_OUTPUT_PATH = "output/jira/"

ALREADY_TESTED = [
    'queries',
    'work_packages',
    'relations',
    'types',
    'versions',
    'users',
    'projects'
]