""""""
import os, asyncio
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastmcp import Client
from starlette.responses import JSONResponse

# ── Where is the MCP server?
# • Dev: import the FastMCP instance directly for 0‑latency in‑memory calls
try:
    from server import mcp                # your FastMCP object (server.py)
    MCP_CLIENT = Client(mcp)              # in‑memory transport
except ImportError:
    # • Prod: talk to a remote MCP HTTP endpoint
    MCP_URL = os.getenv("MCP_URL", "http://mcp:9000/mcp")
    MCP_CLIENT = Client(MCP_URL)          # HTTP transport

app = FastAPI(title="Webhook Ingress")

# Re‑usable helper — keeps each route tiny
async def _call_tool(tool: str, args: dict) -> dict:
    async with MCP_CLIENT:
        return (await MCP_CLIENT.call_tool(tool, args)).data  # returns JSON‑serialisable data

# ────────────────────────────  ROUTES  ──────────────────────────── #

@app.post("/github")
async def github_webhook(req: Request):
    payload = await req.json()
    action  = payload.get("action")
    if not action:
        raise HTTPException(400, "Missing 'action' field")
    # Call the matching MCP tool; your FastMCP server already has the logic
    await _call_tool("github_open_issue_webhook", {"issue_payload": payload})
    return JSONResponse({"status": "ok"})

@app.post("/sendgrid")
async def sendgrid_webhook(req: Request, bg: BackgroundTasks):
    events = await req.json()
    # Slack only needs “200 OK”; do heavy work in the background
    async def process():
        for ev in events:
            await _call_tool(
                "process_sendgrid_event",
                {
                    "event_type": ev["event"],
                    "email":      ev["email"],
                    "reason":     ev.get("reason"),
                },
            )
    bg.add_task(process)
    return JSONResponse({"status": "queued"})  # immediate 200

@app.post("/slack/githubissue")
async def slack_github_issue(req: Request):
    form = await req.form()
    title = form.get("text") or "New Issue from Slack"
    user  = form.get("user_id")
    out   = await _call_tool(
        "create_issue",
        {"title": title, "body": f"Created by Slack user <@{user}>", "slack_user": user},
    )
    return JSONResponse(
        {
            "response_type": "ephemeral",
            "text": f"✅ Created on GitHub: {out['url']}",
        }
    )
