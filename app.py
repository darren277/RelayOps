from sympy import use
from werkzeug import run_simple
from settings import MALFORMED_REQUEST, NO_SUCH_ENDPOINT, SUCCESS, SLACK_UNREACHABLE, PORT
from settings import GITHUB_REPO_OWNER, GITHUB_REPO_NAME, GITHUB_TOKEN
from settings import OPENPROJECT_URL, OPENPROJECT_API_KEY
from settings import LLM_API_KEY
from webhooks.webhooks import openIssueWebhook, closeIssueWebhook, reopenIssueWebhook, create_sendgrid_issue_webhook
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from tasks import process_llm

import json

import gc

import uuid

from pyopenproject.openproject import OpenProject
from pyopenproject.model.project import Project
from pyopenproject.model.work_package import WorkPackage

op = OpenProject(url=OPENPROJECT_URL, api_key=OPENPROJECT_API_KEY)

import requests

from flask import Flask, redirect, request, make_response, jsonify, g, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/endpoints')
def list_routes():
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
        route_info = f"{rule.rule} [{methods}] → {rule.endpoint}"
        output.append(route_info)
    return "<pre>" + "\n".join(sorted(output)) + "</pre>"


@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")


endpoint_case_switch = {
    'open': lambda req: openIssueWebhook(issue=dict(issue=req.json['issue'])).post(),
    'opened': lambda req: openIssueWebhook(issue=dict(issue=req.json['issue'])).post(),
    'closed': lambda req: closeIssueWebhook(issue=dict(issue=req.json['issue'])).post(),
    'reopen': lambda req: reopenIssueWebhook(issue=dict(issue=req.json['issue'])).post()
}

def handle_sendgrid_event(event, event_type):
    unique_id = str(uuid.uuid4())
    g.unique_event_id = unique_id

    webhook = create_sendgrid_issue_webhook(
        event_type,
        event['email'],
        event.get('reason', 'no reason'),
        unique_id
    )
    status = webhook.post()

    del webhook
    gc.collect()

    return status

sendgrid_endpoint_case_switch = {
    event_type: lambda event, et=event_type: handle_sendgrid_event(event, et)
    for event_type in [
        'dropped', 'bounce', 'click', 'open', 'deferred',
        'delivered', 'spamreport', 'unsubscribed'
    ]
}



@app.route('/github', methods=['POST'])
def github_case_switch():
    result = NO_SUCH_ENDPOINT
    action = request.json.get('action')
    if action:
        status_code = endpoint_case_switch.get(action, lambda r: 400)(request)
    else:
        zen = request.json.get('zen')
        if zen == 'Practicality beats purity.':
            result = 'Testing Webhook'
            status_code = 200
        else:
            print('action missing from payload')
            print(request.json)
            result = MALFORMED_REQUEST
            status_code = 400

    if status_code == 200:
        result = SUCCESS
    elif result != NO_SUCH_ENDPOINT:
        result = SLACK_UNREACHABLE
        status_code = 500
    elif status_code == 400:
        print("Something else wrong with request:")
        print(action)

    response = make_response(jsonify(result), status_code)

    response.headers["Content-Type"] = "application/json"
    return response

def create_issue_on_github(title, body):
    url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/issues"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "title": title,
        "body": body,
        # Optionally labels, assignees, etc.
        # "labels": ["slack-created", ...],
        # "assignees": ["your-github-username"],
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code not in [200, 201]:
        print("Error creating GitHub issue:", response.text)
        return False
    else:
        return True

@app.route("/slack/githubissue", methods=["POST"])
def slack_github_issue():
    user_text = request.form.get("text", "")
    user_id = request.form.get("user_id", "")

    issue_title = user_text if user_text else "New Issue from Slack"
    issue_body = f"Created by Slack user <@{user_id}>"
    result = create_issue_on_github(issue_title, issue_body)
    if not result:
        return jsonify({"response_type": "ephemeral", "text": "Error creating issue on GitHub"}), 500

    return jsonify({"response_type": "ephemeral", "text": f"Your issue was created on GitHub: {issue_title}"}), 200


PROJECT_IDS_DICT = {
    'Scrum project': 2
}

TASK_TYPES = {
    'task': 1,
    'milestone': 2
}


def create_new_task(title: str, project_name: str):
    project_id = PROJECT_IDS_DICT[project_name]
    project_search = Project(dict(id=project_id))

    try:
        project = op.get_project_service().find(project_search)
        if project is None:
            raise Exception(f"Project not found: {project_name}")
    except Exception as e:
        raise Exception(f"Failed to fetch project. {e}")
    try:
        task = op.get_work_package_service().create(
            WorkPackage(
                dict(
                    subject=title,
                    project=dict(href=f"/api/v3/projects/{project_id}", title=project_name),
                    type=dict(href=f"/api/v3/types/{TASK_TYPES['task']}", title="task"),
                    description="This is a test task."
                )
            )
        )
        if task is None:
            raise Exception(f"Failed to create task: {title}")
    except Exception as e:
        raise Exception(f"Failed to create task. {e}")
    return task


@app.route("/openproject", methods=["POST"])
def open_project():
    json_data = request.json

    action = json_data.get('action')
    if not action:
        return jsonify({"response_type": "ephemeral", "text": "No action provided"}), 400

    if action == 'work_package:created':
        work_package = json_data.get('work_package')
        subject = work_package.get('subject')
        print(f"New task created: {subject}")
        # TODO: Do other stuff...

    project_title = 'unknown'

    return jsonify({"response_type": "ephemeral", "text": f"Testing: {project_title}"}), 200

@app.route("/slack/openproject", methods=["POST"])
def slack_openproject():
    user_text = request.form.get("text", "")
    user_id = request.form.get("user_id", "")

    task_title = user_text if user_text else "New Task from Slack"
    project_title = "Scrum project"
    result = create_new_task(task_title, project_title)
    if not result:
        return jsonify({"response_type": "ephemeral", "text": "Error creating project on OpenProject"}), 500

    return jsonify({"response_type": "ephemeral", "text": f"Your task {task_title} was created on OpenProject: {project_title}"}), 200


@app.route("/slack/llm_create_task", methods=["POST"])
def slack_llm_create_task():
    user_text = request.form.get("text", "")
    user_id = request.form.get("user_id", "")
    response_url = request.form.get("response_url", "")

    prompt = user_text if user_text else "Test prompt from Slack"

    task = process_llm.delay('llm_create_task', prompt, response_url)
    print('task', task)

    # 3) Return a quick 200 to Slack to avoid timeout
    return jsonify({
        "response_type": "ephemeral",
        "text": "Working on your request... I'll be back with an answer shortly."
    }), 200


@app.route('/slack/llm_wiki', methods=['POST'])
def slack_llm_wiki():
    user_text = request.form.get("text", "")
    user_id = request.form.get("user_id", "")
    response_url = request.form.get("response_url", "")

    prompt = user_text if user_text else "Test prompt from Slack"

    task = process_llm.delay('llm_wiki', prompt, response_url)
    print('task', task)

    # 3) Return a quick 200 to Slack to avoid timeout
    return jsonify({
        "response_type": "ephemeral",
        "text": "Working on your request... I'll be back with an answer shortly."
    }), 200


@app.route('/sendgrid-events', methods=['POST'])
def sendgrid_event_listener():
    events = request.get_json()
    for event in events:
        event_type = event.get('event')

        print(f"Event: {event.get('event')} for {event.get('email')}")
        if event.get('event') == 'dropped': print(f"Reason: {event.get('reason')}")

        handler = sendgrid_endpoint_case_switch.get(event_type)

        if handler:
            status_code = handler(event)
            print(f"SLACK SEND STATUS CODE [{g.unique_event_id}]: {status_code}")
        else:
            print(f"No handler for event type: {event_type}")
    return jsonify({"status": "ok"}), 200


# Pretty print backup JSONs...
@app.route('/backups/<folder>/<filename>')
def backups(folder, filename):
    if filename not in [
        'project_roles.json',
        'projects.json',
        'queries.json',
        'relations.json',
        'types.json',
        'users.json',
        'versions.json',
        'work_packages.json',
        'grids.json'
    ]:
        raise Exception("No such file.")
    with open(f'output/{folder}/{filename}', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)


@app.route('/op_grid')
def op_grid():
    return render_template('op_grid.html')


from dashboard import register_dash_app

@app.route('/dashboard')
def render_dashboard():
    return redirect('/dash')


dash_app = register_dash_app(app)

#application = DispatcherMiddleware(app, {'/dash': dash_app.server})

application = dash_app

if __name__ == '__main__':
    #run_simple('0.0.0.0', PORT, application, use_reloader=True, use_debugger=True)
    application.run('0.0.0.0', PORT, debug=True)
