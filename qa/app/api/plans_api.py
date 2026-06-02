from app.api.api_client import APIClient
from models.plan_model import Plan


class PlansAPI:
    """API client for membership plans endpoints."""

    def __init__(self, client: APIClient) -> None:
        self.client = client

    def get_plans(self) -> list[Plan]:
        """Fetches list of active membership plans."""
        response = self.client.request("GET", "/api/v1/plans")
        assert isinstance(response, list)
        
        plans = []
        for plan in response:
            plans.append(Plan(
                id=plan["id"],
                name=plan["name"],
                type=plan["type"],
                price=plan["price"],
                duration_days=plan["duration_days"],
                visit_limit=plan.get("visit_limit"),
                max_freeze_days=plan["max_freeze_days"],
                max_freeze_count=plan["max_freeze_count"],
                is_active=plan["is_active"]
            ))
        return plans
