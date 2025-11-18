from typing import List

from pydantic import BaseModel

from kontxt.task_state import TaskState
from kontxt.tool_call import ToolCall


class PlanItem(BaseModel):
    state: TaskState = TaskState.PENDING
    task: str
    tool_calls: List[ToolCall] = []

    def to_string(self) -> str:
        tool_call_results = "\n".join([t.to_string() for t in self.tool_calls])
        return f"""{self.plan_state} {self.task}{tool_call_results}"""
