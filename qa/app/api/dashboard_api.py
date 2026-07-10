from app.api.api_client import APIClient
from models.dashboard_model import DashboardResponse, KPICard, KPINotation, AttendanceStats, ExpiringMember


class DashboardAPI:
    """API client for dashboard operations."""

    def __init__(self, client: APIClient) -> None:
        self.client = client

    def get_dashboard(self) -> DashboardResponse:
        """Fetches dashboard stats and returns a typed DashboardResponse."""
        response = self.client.request("GET", "/api/v1/dashboard")
        assert isinstance(response, dict)

        kpis = []
        for card in response.get("kpis", []):
            delta_data = card.get("delta")
            delta = KPINotation(**delta_data) if delta_data else None
            kpis.append(KPICard(
                label=card["label"],
                value=card["value"],
                unit=card.get("unit"),
                delta=delta,
                spark=card.get("spark", [])
            ))

        att = response.get("attendance", {})
        attendance = AttendanceStats(
            current=att.get("current", []),
            previous=att.get("previous", []),
            y_max=att.get("y_max", 120),
            x_labels=att.get("x_labels", [])
        )

        expiring = []
        for m in response.get("expiring", []):
            expiring.append(ExpiringMember(
                id=m["id"],
                name=m["name"],
                initials=m["initials"],
                plan=m["plan"],
                days_left=m["days_left"],
                expires_on=m["expires_on"],
                avatar_gradient=m["avatar_gradient"]
            ))

        return DashboardResponse(kpis=kpis, attendance=attendance, expiring=expiring)
