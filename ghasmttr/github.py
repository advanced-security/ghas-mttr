import os
import json
import requests
from requests_cache import CachedSession
from string import Template
from ghasmttr.utils.get import get


GQUERY_COMMIT_HISTORY = """\
{
  repository(owner: "$owner", name: "$repo") {
    defaultBranchRef {
      target {
        ... on Commit {
          history(since: "$created_at") {
            pageInfo {
              hasNextPage
              endCursor
            }
            edges {
              node {
                oid
                pushedDate
              }
            }
          }
        }
      }
    }
  }
}
"""


class GitHub:
    def __init__(
        self,
        owner: str,
        name: str = None,
        instance: str = "https://github.com",
        token: str = None,
    ):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "token " + token,
        }
        self.instance = instance

        if instance == "https://github.com":
            self.instance_api = "https://api.github.com"
        else:
            raise Exception("Server URL not supported right now")

        self.token = token

        self.owner = owner
        self.name = name

        #  Crazy 1 day cache time
        self.session = CachedSession(
            expire_after=86400, allowable_methods=["GET", "POST"]
        )

    @property
    def repository(self):
        return f"{self.owner}/{self.name}"

    def getRepositories(self):
        url = f"{self.instance_api}/orgs/{self.owner}/repos"
        return self.getRequest(url)

    def getSecurityIssues(self, repository: str, ref: str = None):

        url = (
            f"{self.instance_api}/repos/{self.owner}/{repository}/code-scanning/alerts"
        )
        print(f"Getting Security Results for :: {self.owner}/{repository}")
        data = self.getRequest(url)
        return data

    def createSummaryIssue(
        self, repository: str, title: str, body: str, assignees: list[str] = []
    ):
        owner, repo = repository.split("/")

        url = f"{self.instance_api}/repos/{owner}/{repo}/issues"

        data = {"title": title, "body": body, "assignees": assignees}

        response = requests.post(url, headers=self.headers, json=data)

        return response.json()

    def findFixByCommit(self, repository: str, commit: str, created_at: str):
        variables = {
            "owner": self.owner,
            "repo": repository,
            "commit": commit,
            "created_at": created_at,
        }

        data = self.getGQLRequest(GQUERY_COMMIT_HISTORY, variables=variables)
        #  Get the edges of history
        history = get("data.repository.defaultBranchRef.target.history.edges", data)

        index = 0
        fix_commit = None
        #  Get the "child" of the last know fix
        #  TODO: Reversing the histroty before checking?
        for cmmt in history:
            oid = cmmt.get("node", {}).get("oid")
            if oid == commit:
                #  Get the child (previous index)
                fix_commit = history[index - 1].get("node", {})
                break
            index += 1

        if fix_commit is None:
            # raise Exception(f"Could not find commit: {commit}")
            return {}

        return fix_commit

    def getRequest(self, url: str, optional_params: dict = {}):
        results = []

        # print(f"Request URL :: {url}")

        page_counter = 1
        per_page = 100

        while True:
            response = self.session.get(
                url,
                headers=self.headers,
                params={"page": page_counter, "per_page": per_page},
            )

            #  TODO: Check limits here (200 => pause)

            if response.status_code != 200:
                return None

            results.extend(response.json())

            if len(response.json()) < per_page:
                break
            page_counter += 1

        return results

    def getGQLRequest(self, query: str, variables: dict):

        query = Template(query).substitute(**variables)

        response = self.session.post(
            "https://api.github.com/graphql",
            json={"query": query},
            headers=self.headers,
        )
        return response.json()
