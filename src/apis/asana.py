# packages

import requests

# Asana API Class


class AsanaAPI:
    """
    Simple Asana API client for retrieving and manipulating tasks, projects, and teams.
    Requires a Personal Access Token (PAT).
    """
    BASE_URL = "https://app.asana.com/api/1.0"

    def __init__(self, personal_access_token: str):
        """
        Initialize the Asana client.
        """
        if not personal_access_token:
            raise ValueError(
                "A valid Asana personal access token is required.")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {personal_access_token}",
            "Content-Type": "application/json"
        })

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, data: dict) -> dict:
        url = f"{self.BASE_URL}{path}"
        resp = self.session.post(url, json={"data": data})
        resp.raise_for_status()
        return resp.json()

    def _put(self, path: str, data: dict) -> dict:
        url = f"{self.BASE_URL}{path}"
        resp = self.session.put(url, json={"data": data})
        resp.raise_for_status()
        return resp.json()

    def get_projects(self, workspace: str = None, team: str = None) -> list:
        """
        Retrieve a list of projects in a workspace or team.
        """
        params = {}
        if workspace:
            params['workspace'] = workspace
        if team:
            params['team'] = team
        return self._get("/projects", params).get('data', [])

    def get_tasks(self, project_gid: str, completed_since: str = "now") -> list:
        """
        Retrieve tasks in a given project.
        """
        params = {'project': project_gid, 'completed_since': completed_since}
        return self._get("/tasks", params).get('data', [])

    def get_task_details(self, task_gid: str, opt_fields: list = None) -> dict:
        """
        Retrieve detailed information about a specific task.
        """
        params = {}
        if opt_fields:
            params['opt_fields'] = ",".join(opt_fields)
        return self._get(f"/tasks/{task_gid}", params).get('data', {})

    def create_task(self, name: str, project_gid: str, assignee: str = None, notes: str = None, due_on: str = None) -> dict:
        """
        Create a new task in Asana.
        """
        data = {"name": name, "projects": [project_gid]}
        if assignee:
            data['assignee'] = assignee
        if notes:
            data['notes'] = notes
        if due_on:
            data['due_on'] = due_on
        return self._post("/tasks", data).get('data', {})

    def complete_task(self, task_gid: str) -> dict:
        """
        Mark a task as completed.
        """
        return self._put(f"/tasks/{task_gid}", {"completed": True}).get('data', {})

    def update_task(self, task_gid: str, name: str = None, notes: str = None,
                    assignee: str = None, due_on: str = None) -> dict:
        """
        Update one or more fields of a task.
        """
        data = {}
        if name is not None:
            data['name'] = name
        if notes is not None:
            data['notes'] = notes
        if assignee is not None:
            data['assignee'] = assignee
        if due_on is not None:
            data['due_on'] = due_on
        if not data:
            raise ValueError("At least one field must be provided to update.")
        return self._put(f"/tasks/{task_gid}", data).get('data', {})

    def get_users(self, workspace: str) -> list:
        """
        List users in a workspace.
        """
        params = {'workspace': workspace}
        return self._get("/users", params).get('data', [])
