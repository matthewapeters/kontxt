import json
from typing import Any, Dict

from pydantic import BaseModel


class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any]
    result: str

    def to_string(self) -> str:
        return f"""
    * Tool: {self.name}
        * Args: {json.dumps(self.args)}
        * Result:
        ```
        {self.result}
        ```"""
