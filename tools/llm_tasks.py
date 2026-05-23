""""""
import asyncio, os, httpx
from fastmcp import FastMCP, Context
from fastmcp.tools.tool import ToolResult

from mcp_init import mcp

OPENAI_KEY = os.getenv("LLM_API_KEY")

@mcp.tool(tags={"llm", "openai"})
async def llm_create_task(prompt: str,
                          project: str = "Scrum project",
                          ctx: Context | None = None) -> ToolResult:
    """
    Use the LLM to turn an English prompt into an OpenProject task.
    Progress updates are streamed back to the client.
    """
    ctx.report_progress(message="Contacting model…", percent=10)

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
            json={"model": "gpt-4o", "messages": [
                {"role": "user", "content": prompt},
                {"role": "system", "content": "Return a concise task title"}
            ]}
        )
    task_title = resp.json()["choices"][0]["message"]["content"].strip()
    ctx.report_progress(message="Creating task…", percent=80)

    # reuse OpenProject helper (not shown)
    wp_url = create_openproject_task(task_title, project)
    ctx.report_progress(message="Done", percent=100)

    return ToolResult(
        content=[f"✅ Created *{task_title}* in {project} – {wp_url}"],
        structured_content={"title": task_title, "url": wp_url},
    )
