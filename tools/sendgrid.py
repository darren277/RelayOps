""""""
from mcp_init import mcp

import uuid, gc
from fastmcp import FastMCP

from .github import create_issue

@mcp.tool(name="process_sendgrid_event", tags={"sendgrid"})
def process_sendgrid_event(event_type: str,
                           email: str,
                           reason: str | None = None) -> str:
    """
    Turn a SendGrid event into a GitHub issue; returns the issue URL.
    """
    unique_id = str(uuid.uuid4())
    title = f"[SendGrid:{event_type}] {email}"
    body  = f"Reason: {reason or 'N/A'}\nEvent ID: {unique_id}"
    issue_data = create_issue(title=title, body=body)
    # explicit teardown matches your GC pattern
    gc.collect()
    return issue_data["url"]
