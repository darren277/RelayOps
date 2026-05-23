""""""
from mcp_init import mcp

from typing import Optional
import os
from pyopenproject.openproject import OpenProject
from pyopenproject.model.project import Project
from pyopenproject.model.work_package import WorkPackage

OPENPROJECT_URL = os.getenv("OPENPROJECT_URL")
OPENPROJECT_API_KEY = os.getenv("OPENPROJECT_API_KEY")

PROJECT_IDS_DICT = {
    "Scrum project": 2
}

TASK_TYPES = {
    "task": 1,
    "milestone": 2
}

op = OpenProject(url=OPENPROJECT_URL, api_key=OPENPROJECT_API_KEY)


@mcp.tool(tags={"openproject"})
def create_openproject_task(title: str,
                            project_name: str = "Scrum project",
                            description: Optional[str] = None) -> str:
    """
    Create a new task in OpenProject with the given title and project name.
    """
    if project_name not in PROJECT_IDS_DICT:
        raise ValueError(f"Unknown project: {project_name}")

    project_id = PROJECT_IDS_DICT[project_name]
    project = Project(dict(id=project_id))

    try:
        op.get_project_service().find(project)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch project: {e}")

    try:
        task = op.get_work_package_service().create(
            WorkPackage(
                dict(
                    subject=title,
                    project=dict(href=f"/api/v3/projects/{project_id}", title=project_name),
                    type=dict(href=f"/api/v3/types/{TASK_TYPES['task']}", title="task"),
                    description=description or "Auto-created task"
                )
            )
        )
    except Exception as e:
        raise RuntimeError(f"Failed to create task: {e}")

    return f"{OPENPROJECT_URL}/work_packages/{task.id}"
