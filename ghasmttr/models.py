from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class SecurityAlert:
    id: str
    state: str
    #  Security rule name
    rule: str
    tool: str
    # Dates and Times
    created: str
    remediated: str = None

    last_commit: str = None

    @property
    def time_to_remediate(self):
        if self.remediated is None:
            return None
        alert_creation_time = datetime.strptime(self.created, "%Y-%m-%dT%XZ")
        alert_remediated_time = datetime.strptime(self.remediated, "%Y-%m-%dT%XZ")

        return alert_remediated_time - alert_creation_time


@dataclass
class RepositorySecurityAlerts:
    alerts: list[SecurityAlert] = field(default_factory=list)

    def append(self, alert: SecurityAlert):
        self.alerts.append(alert)

    def findById(self, id: int) -> SecurityAlert:
        for alrt in self.alerts:
            if alrt.id == id:
                return alrt

    def getClosed(self):
        results: list[SecurityAlert] = []
        for alert in self.alerts:
            if alert.state == "dismissed":
                results.append(alert)
            elif alert.state == "fixed" and alert.remediated:
                results.append(alert)
        return results

    def createAlert(self, **data):
        # https://docs.github.com/en/rest/reference/code-scanning#list-code-scanning-alerts-for-a-repository
        if data.get("dismissed_at") is not None:
            remediated = data.get("dismissed_at")
        else:
            remediated = data.get("fixed_at")

        alert = SecurityAlert(
            id=data.get("number"),
            state=data.get("state"),
            rule=data.get("rule", {}).get("name"),
            tool=data.get("tool", {}).get("name"),
            created=data.get("created_at"),
            remediated=remediated,
            last_commit=data.get("most_recent_instance", {}).get("commit_sha"),
        )
        return alert

    def addAndCreateAlert(self, **data):
        self.append(self.createAlert(**data))

    def getTTR(self):
        deltatimes = [alert.time_to_remediate for alert in self.getClosed()]
        if len(deltatimes) == 0:
            return timedelta(0)
        return sum(deltatimes, timedelta(0)) / len(deltatimes)


@dataclass
class Repository:
    owner: str
    name: str

    total: int = 0
    open: int = 0
    closed: int = 0

    mttr: str = None

    @property
    def repository(self):
        return f"{self.owner}/{self.name}"
