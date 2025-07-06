# About

This is a relay station for webhooks, currently predominantly GitHub and Slack.

This is also my first attempt at using an abstract factory pattern for easier extensibility.

This is a work in progress.

**Please note:** LLM tool calls are very experimental at the moment.

## MCP

Check out the very early draft of the **Model Context Protocol (MCP)** that I am using to define the envelope for all messages exchanged through this relay station: [docs/MCP.md](docs/MCP.md).

# Usage

1. Configure webhook for a GitHub repository (see Notes below).
![](RepoWebhooks.png)

2. Configure webhook for a Slack channel.
Check out the following resource for details:
https://api.slack.com/messaging/webhooks

3. Clone repository.

4. Create a `.env` file for:
   - `SLACK_RELAY_ENDPOINT`: The endpoint for all Slack messages (ex: "https://hooks.slack.com/services/{STRING1}/{STRING2}/{STRING3}").
   - `GITHUB_REPO`: Repository to monitor for changes (ex: "https://github.com/darren277/githubtoslack/").
   - `PORT`: Flask port.

5. Create a virtual environment.
   - For example, on Ubuntu:
   1. `python3 -m venv venv`.
   2. `source venv/bin/activate`.

6. Install dependencies.
   1. `pip3 install -r requirements.txt`.

7. Run `python3 app.py`.

## Slack to GitHub

Provision a personal access token from GitHub Developer Settings.

Configure the slash command from https://api.slack.com/apps/<APP_ID>/slash-commands.

`/githubissue Fix user login bug`.

## LLM Endpoint

Don't forget to install RabbitMQ:

```shell
sudo apt-get install rabbitmq-server
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server
```

To troubleshoot, check the logs:

```shell
celery -A tasks.celery worker --loglevel=info
```

# Notes

Mine is deployed on an AWS EC2 instance so that GitHub has a remote URL to send to.

Safely testing locally would almost require a tunneling service like ngrok.

## LLM Use Cases

### Structured Outputs

I encountered an interesting scenario today. I was originally intending to use `pydantic` to define a structured model for OpenProject `WorkPackage` objects (i.e. Tasks, etc) that would be passed directly into the OpenAI chat completions API call. What occured instead, however, was I discovered a certain complication due to having multiple fundamentally different kinds of tool calls available, making structured output definitions trickier.

So what happened instead, was that I wound up creating a third tool call option, wherein I simply use a `pydantic` builtin method to convert the input to the desired structured output. It is experimental for the time being, so we'll see how it works.

### Multiple Tools

It turns out that incorporating numerous fundamentally different kinds of tool calls can make things a bit messy.

For example, I found that the LLM was using tools that I really did not see as all that relevant for the given query.

### Example Task Creation

As of right now, it unfortunately needs a pretty precise definition of some attributes in order to behave consistently. This is something I will experiment with as I go.

Slack slash command example: `/llm create the following task: Title: "Fix User Sign-Up Issue". Start date: 2025-02-20. Due date: 2025-02-28. Estimated time: 5 hours.`.

# TODO

- Programmatically list endpoints.
- Proper exception handling and logging.
- Add more webhook types.


## OpenProject API

Consider validating attributes before sending request for a cleaner error experience.

```json
{
   "_type":"Error",
   "errorIdentifier":"urn:openproject-org:api:v3:errors:MultipleErrors",
   "message":"Multiple field constraints have been violated.",
   "_embedded":
    {
       "errors":
        [
           {
              "_type":"Error",
              "errorIdentifier":"urn:openproject-org:api:v3:errors:PropertyConstraintViolation",
              "message":"Project can't be blank.",
              "_embedded":{"details":{"attribute":"project"}}
           },
           {
              "_type":"Error",
              "errorIdentifier":"urn:openproject-org:api:v3:errors:PropertyConstraintViolation",
              "message":"Type can't be blank.",
              "_embedded":{"details":{"attribute":"type"}}
           }
        ]
    }
}
```

## SurrealDB

To run: `docker run --rm --pull always -p $(EXT_PORT):$(INT_PORT) surrealdb/surrealdb:latest start`.

I will be using `EXT_PORT=8011` and `INT_PORT=8011` for both the external and internal port, but you can change this to whatever you like.

To run (hardcoded port): `docker run --rm --pull always -p 8011:8011 surrealdb/surrealdb:latest start --bind 0.0.0.0:8011 --user root --pass root`.

### Migrations

To migrate the Wiki data (for vector-based RAG search):

Step 1: Export Wiki as an HTML file from OpenProject.

Step 2: Run the migration script (HTML filename is currently hardcoded. Will convert to a CLI argument later).

```shell
python3 migrations.py
```

Note that you have to use the same embedding model for both the migration and the search queries.
