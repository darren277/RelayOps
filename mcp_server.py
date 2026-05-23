""""""
# --- import side‑effect modules that register tools ---
from mcp_init import mcp

from tools import github, openproject, sendgrid, slack, llm_tasks   # noqa: F401

print("HELLO!")

if __name__ == "__main__":
    #asgi_app.run() # uvicorn‑style run; supports --port etc.
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=9000,
        path="/mcp",  # <-- sets the root path of the API
        log_level="debug"
    )
