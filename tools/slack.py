""""""
from mcp_init import mcp

from typing import Optional
from tools.github import create_issue
from tools.openproject import create_openproject_task
from tools.llm_tasks import llm_create_task
from fastmcp import Context
from fastmcp.tools.tool import ToolResult

@mcp.tool(tags={"slack", "github"})
def slack_create_github_issue(user_id: str, text: str = "") -> str:
    """
    Slack command to create a GitHub issue.
    """
    title = text or "New Issue from Slack"
    body = f"Created by Slack user <@{user_id}>"
    result = create_issue(title=title, body=body, slack_user=user_id)
    return f"✅ Issue created: {result['url']}"

@mcp.tool(tags={"slack", "openproject"})
def slack_create_openproject_task(user_id: str, text: str = "") -> str:
    """
    Slack command to create an OpenProject task.
    """
    task_title = text or "New Task from Slack"
    url = create_openproject_task(title=task_title, project_name="Scrum project")
    return f"✅ Task created in OpenProject: {url}"

@mcp.tool(tags={"slack", "llm"}, name="slack_llm_create_task")
async def slack_llm_create_task(user_id: str,
                                text: str = "",
                                ctx: Optional[Context] = None) -> ToolResult:
    """
    Slack LLM tool: Generate and create a task based on natural language input.
    """
    prompt = text or "Generate a task from Slack input"
    result = await llm_create_task(prompt, "Scrum project", ctx)
    return result
