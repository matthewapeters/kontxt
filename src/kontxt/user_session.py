from typing import List

from pydantic import BaseModel

from kontxt.plan_item import PlanItem


class UserSession(BaseModel):
    plan: List[PlanItem]
    user: str
    context: List[str] = []
