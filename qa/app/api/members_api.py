from app.api.api_client import APIClient
from models.member_model import MembersResponse, MemberItem


class MembersAPI:
    """API client for members management endpoints."""

    def __init__(self, client: APIClient) -> None:
        self.client = client

    def get_members(self) -> MembersResponse:
        """Fetches the list of all members and returns a typed MembersResponse."""
        response = self.client.request("GET", "/api/v1/members")
        assert isinstance(response, dict)
        
        items = []
        for item in response.get("items", []):
            items.append(MemberItem(
                id=item["id"],
                full_name=item["full_name"],
                phone=item["phone"],
                initials=item["initials"],
                status=item["status"],
                plan_name=item["plan_name"],
                plan_type=item["plan_type"],
                expires_on=item["expires_on"],
                days_left=item["days_left"],
                visits_remaining=item.get("visits_remaining"),
                visit_limit=item.get("visit_limit")
            ))
            
        return MembersResponse(
            items=items,
            total=response.get("total", 0),
            counts_by_status=response.get("counts_by_status", {})
        )
