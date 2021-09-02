import os
import argparse
from dataclasses import dataclass

from ghasmttr.__version__ import *
from ghasmttr.github import GitHub
from ghasmttr.exporters import __EXPORTERS__
from ghasmttr.models import *

__HERE__ = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(__name__)

parser.add_argument("-c", "--config")
parser.add_argument("--owner", default=os.environ.get("GITHUB_REPOSITORY_OWNER"))
parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
parser.add_argument("-t", "--token", default=os.environ.get("GITHUB_TOKEN"))

parser.add_argument("--exporter", default="issue_summary", help="Exporter name")
parser.add_argument("--exporter-list", action="store_true", help="Exporter list")

parser.add_argument(
    "--output", default=os.path.join(__HERE__, ".mttr"), help="Output folder"
)
parser.add_argument(
    "--template-path",
    default=os.path.join(__HERE__, "templates"),
    help="Template folder",
)
parser.add_argument(
    "--instance",
    default=os.environ.get("GITHUB_SERVER_URL", "https://github.com"),
)


if __name__ == "__main__":
    arguments = parser.parse_args()

    if arguments.exporter_list:
        for exporter, exporter_func in __EXPORTERS__.items():
            print(f" >> Exporter :: {exporter}")

        exit(0)

    owner, repo = arguments.repository.split("/")

    github = GitHub(
        owner=owner,
        name=repo,
        instance=arguments.instance,
        token=arguments.token,
    )

    print(f"GitHub Repository :: {github.repository}")

    print(f"Exporter :: {arguments.exporter}")

    # repositories = [{"name": "AutoBuilder"}]

    repositories = github.getRepositories()
    print(f"Total Repositories :: {len(repositories)}")

    repositories_results = []

    print("::group::Processing Repositories")

    for repo in repositories:
        repository_name = repo.get("name")
        # print(f"Processing :: {repository_name}")

        repository = Repository(owner, repository_name)

        results = github.getSecurityIssues(repository_name)

        if results:
            security_alerts = RepositorySecurityAlerts()

            for result in results:
                alert = security_alerts.createAlert(**result)

                if alert.state == "fixed":
                    alert.remediated = github.findFixByCommit(
                        repository.name, alert.last_commit, alert.created
                    ).get("pushedDate")

                security_alerts.alerts.append(alert)

            repository.total = len(security_alerts.alerts)
            repository.closed = len(security_alerts.getClosed())
            repository.open = repository.total - repository.closed

            repository.mttr = security_alerts.getTTR()

            print(f"{repository}")
            # print(f"Time to Remediate :: {repository.mttr}")
        else:
            # print("Skipping as not security issues...")
            pass

        repositories_results.append(repository)

    print("::endgroup::")

    for exporter, exporter_func in __EXPORTERS__.items():
        if exporter == arguments.exporter or arguments.exporter == "all":
            print(f" >> Exporter :: {exporter}")
            exporter_func(
                github=github,
                repositories=repositories_results,
                template_path=arguments.template_path,
            )
