# Model Context Protocol (MCP) — Relay Station Draft 0.1

## 1. Purpose & Scope

This draft defines a **Model Context Protocol (MCP)** for our Python Flask relay station that brokers messages between external webhooks (Slack, GitHub Issues/PRs, Sentry, OpenProject, etc.), local LLM agents, and human overseers. Its goals are to

1. Provide a *uniform envelope* for all messages, independent of source.
2. Preserve enough metadata for deterministic hand-offs, RAG look-ups, memory writes, and tool calls.
3. Keep the schema minimal so that transformation shims are small and easy to maintain.

---

## 2. Core Concepts

| Concept              | Description                                                                                                             |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **Envelope**         |  JSON object that wraps *all* content exchanged through the relay.                                                      |
| **Role**             |  `user`, `assistant`, `tool`, or `system` — same semantics as OpenAI / Anthropic chat, but extended to non-LLM senders. |
| **Channel**          |  Origin or destination integration (e.g. `slack`, `github`, `sentry`, `openproject`, `internal`).                       |
| **Context Layers**   |  `system` (policy), `session` (conversation/thread), `task` (ephemeral), and `live` (the current turn).                 |
| **Tool Call Object** |  Declarative request or result from a structured function/tool invocation.                                              |
| **Memory Slots**     |  Named stores (`episodic`, `long_term`) that can be attached to or extracted from a message.                            |
| **Retrieval Refs**   |  URIs or IDs of documents retrieved via RAG for this turn.                                                              |

---

## 3. MCP Message JSON Schema (abridged)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MCPMessage",
  "type": "object",
  "properties": {
    "id":          {"type": "string", "description": "UUID v4"},
    "timestamp":   {"type": "string", "format": "date-time"},
    "channel":     {"type": "string", "enum": ["slack", "github", "sentry", "openproject", "internal"]},
    "role":        {"type": "string", "enum": ["user", "assistant", "tool", "system"]},

    "context": {
      "type": "object",
      "properties": {
        "system":   {"type": "string", "description": "High-level policy or guardrails."},
        "session":  {"type": "string", "description": "Conversation/thread summary."},
        "task":     {"type": "string", "description": "Short-lived task description."}
      }
    },

    "content": {"type": "string", "description": "Natural-language payload."},

    "tool_call": {
      "type": ["object", "null"],
      "properties": {
        "name": {"type": "string"},
        "args": {"type": "object"},
        "result": {"type": ["object", "null"]}
      }
    },

    "memory_update": {
      "type": ["object", "null"],
      "properties": {
        "kind": {"type": "string", "enum": ["episodic", "long_term"]},
        "data": {"type": "object"},
        "ttl":  {"type": "integer", "description": "Seconds until expiry (optional)."}
      }
    },

    "retrieval_refs": {
      "type": "array",
      "items": {"type": "string"}
    },

    "meta": {"type": "object"}
  },
  "required": ["id", "timestamp", "channel", "role", "content"]
}
```

### Notes

* **Extensibility** — Non-breaking: new optional fields allowed.
* **Token-Budget Tags** — `meta.budget` (estimate), supports truncation heuristics.

---

## 4. Message Flow Example

1. **Slack → Relay**

   1. Slack slash-command hits webhook.
   2. Flask shim converts payload → `MCPMessage` (`channel: "slack"`, `role: "user"`).
   3. Message pushed onto internal queue.
2. **LLM Agent** pulls message, decides to call *SummarizeIssue* tool.

   1. Emits `MCPMessage` with `role:"assistant"`, embedding `tool_call`.
3. **Tool Runner** executes `SummarizeIssue`, posts *result* as `tool` message.
4. **Human Supervisor** sees assistant suggestion in Slack, edits, then approves.
5. Relay converts approval into GitHub comment webhook (channel: `github`).

> **Tip**: Keep the *same* `task` ID across these messages so the thread stitches together for RAG.

---

## 5. Context Layer Rules

| Layer       | Lifetime                   | Storage                      | Truncation           |
| ----------- | -------------------------- | ---------------------------- | -------------------- |
| **system**  |  Static (per deployment)   | Env/config file              | Never                |
| **session** |  Up to 100 turns or 24 h   | Redis key `session:{thread}` | Summarize after 2 KB |
| **task**    |  Ephemeral (minutes-hours) | In-memory dict               | Drop when done       |
| **live**    |  Current message           | n/a                          | n/a                  |

---

## 6. Memory Handling

* `memory_update.kind == "episodic"` ⇒ store keyed by `thread_id`.
* `memory_update.kind == "long_term"` ⇒ vector-DB upsert with recency scoring.

---

## 7. Retrieval-Augmented Generation (RAG)

* When the agent calls `retrieve_docs(query, k)` the runner returns `retrieval_refs` list.
* The assistant *must* cite each ref in its `content` using `[[ref:id]]` so downstream channels can render links.

---

## 8. Tool Invocation Contract

```json
{
  "name": "SummarizeIssue",
  "args": {"issue_url": "https://github.com/org/repo/issues/123"},
  "result": {
    "summary": "…",
    "labels": ["bug", "critical"]
  }
}
```

* `result` is **null** until the tool runner responds.
* A failed tool run sets `result.error` and triggers fallback routing.

---

## 9. Webhook Integration Cheat-Sheet

| Integration     | Inbound Mapper  | Outbound Formatter |
| --------------- | --------------- | ------------------ |
| **Slack**       | `slack→mcp.py`  | `mcp→slack.py`     |
| **GitHub**      | `github→mcp.py` | `mcp→github.py`    |
| **Sentry**      | `sentry→mcp.py` | `mcp→sentry.py`    |
| **OpenProject** | `op→mcp.py`     | `mcp→op.py`        |

---

## 10. Security & Privacy

* Strip PII before writing to `long_term` memory.
* Sign/encrypt outbound webhooks when supported.

---

## 11. Versioning

* `meta.mcp_version` — semantic version string.
* Breaking changes increment **MAJOR**.

---

### Next Steps

1. Wire the inbound/outbound mappers.
2. Add middleware that enforces truncation & summarization rules.
3. Instrument for metrics (latency, failures).
4. Are the *role/channel* enums sufficient for our endpoints?
5. Should we support nested tool calls?
