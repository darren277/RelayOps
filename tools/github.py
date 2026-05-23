""""""
import requests, os
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult

from mcp_init import mcp

GITHUB_API = "https://api.github.com"
REPO_OWNER  = os.getenv("GITHUB_REPO_OWNER")
REPO_NAME   = os.getenv("GITHUB_REPO_NAME")
TOKEN       = os.getenv("GITHUB_TOKEN")

@mcp.tool(tags={"slack", "github"})
def create_issue(title: str,
                 body: str | None = None,
                 slack_user: str | None = None) -> dict:
    """
    Create a GitHub issue and return its URL.
    """
    resp = requests.post(
        f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/issues",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        },
        json={"title": title,
              "body": body or f"Created by Slack user {slack_user}"},
        timeout=10,
    )
    resp.raise_for_status()
    url = resp.json()["html_url"]
    # returning a dict gives us automatic structured output
    return {"url": url, "title": title}
