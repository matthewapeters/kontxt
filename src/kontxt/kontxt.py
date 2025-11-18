import json
import logging
from typing import Dict, List
from uuid import uuid1

import requests

from kontxt.tool_call import ToolCall
from kontxt.user_session import UserSession
from kontxt.task_state import TaskState
from kontxt.plan_item import PlanItem

MAX_CONTEXT_TOKENS = 4096
MODEL = "gpt-oss"
OLLAMA_API_URL = "http://localhost:11435/api/generate"
KONTXT_API_URL = "http://localhost:8001/"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Kontxt:
    _context: Dict[str, UserSession] = {}
    _key: str = ""
    _curration_status: bool = False

    @property
    def curration_status(self):
        return self._curration_status

    @curration_status.setter
    def curration_status(self, stat: bool):
        self._curration_status = stat

    @property
    def session(self) -> UserSession:
        return self._context[self._key]

    @session.setter
    def session(self, sess: UserSession):
        self._key = uuid1()
        self._context[self._key] = sess

    @property
    def plan(self) -> List[str]:
        return self.session.plan

    @plan.setter
    def plan(self, plan: List[str]):
        logger.debug(f"Plan added: {plan}")
        self.session.plan = plan

    @property
    def plan_str(self) -> str:
        # if the number of plans match the number of user-requests, then return the most recent plan as a string
        if len(self.session):
            return "\n".join(self.plan)
        return "* Agent should define a detailed plan for the user's request"

    @property
    def user(self):
        return self.session.user

    @user.setter
    def user(self, user_message):
        self.session.user = user_message

    @property
    def context(self) -> List[str]:
        return self.session.context

    @context.setter
    def context(self, context: List[str]):
        self.session.context = context

    def add_context(self, context: str):
        """add something to the end of the context"""
        self.session.context.append(context)

    @property
    def context_str(self) -> str:
        """Returns a bullet-pointed sstring representation of the current context."""
        return "\n".join([f"* {c}" for c in self.context])

    @property
    def summary(self) -> str:
        """Returns a bullet-pointed sstring representation of the current Kontxt state."""
        return f"""
## User
{self.user}

## Plan
{self.plan_str}

## Context
{self.context}
"""

    @property
    def currator_prompt(self) -> str:
        """Returns the templated instructions for the Context Currator"""

        return f"""
# Agent Directive

[CRITICAL] Follow these instructions systematically

## System

[START SYSTEM]

You are Kontxt, a Context Orchestrator AI.
Your job is to curate the minimal yet complete context needed for the LLM to
answer the user’s request.
The context must not exceed {MAX_CONTEXT_TOKENS} tokens.

Respond only in JSON following this schema:

### Response Schema

```json
{{
"User": string,
"Plan": [
{{
"status": string,
"description": string,
"tool_calls": [{{
"status": string,
"name": string,
"args": list[string],
"results": list[string]}},
...
]}},
...
],
"Context": [string],
"CurationStatus": string
}}
```

* **User** - the original user prompt.
* **Plan** - step-by-step plan. Each item starts with a status:
  * `[ ]` - pending
  * `[✔]` - completed
  * `[X]` - failed
  * `tool_calls` lists the tools needed for that step.
* **Context** - the current work-in-progress context.
* **CurationStatus** - overall status of the plan, starting `[ ]` and marked `[✔]`
  when the context is ready for the LLM.

### Tool Calls

* Use tools to gather data, filter, summarize, or off-load content.
* If no tools are required, return an empty list.
* If a task is not complete, but there are results in the tool_calls that
inform the task, additional tool_calls may be added until adequate result
data is available to mark the task as complete.

### Example

```json
{{
  "status":"[ ]",
  "description":"Find tool to read './data.txt'.",
  "tool_calls":[
    {{"name":"tools","args":[]}},
    {{"name":"tools","args":["filesystem-tools"]}}
  ]
}}
```

[INSIGHT] The MCP marks tool_call status, the context currator updates the task status

[END SYSTEM]

## Plan
{self.plan_str}

## Context
{self.context_str}

## User
{self.user}
"""

    def query_ollama(self):
        """Prompt the ollama service to currate the context for the LLM"""

        logger.debug(f"Prompt sent to Ollama: {self.currator_prompt}")
        service_response_json = requests.post(
            OLLAMA_API_URL,
            json={
                "model": MODEL,
                "prompt": self.currator_prompt,
                "stream": False,
            },
            timeout=120,
        ).json()
        logger.debug(f"Ollama Response JSON: {service_response_json}")

        model_response_raw = service_response_json.get("response", "")
        if model_response_raw == "":
            raise RuntimeError("No response from ollama service")
        model_response = json.loads(model_response_raw)

        self.curration_status = model_response.get("CurrationStatus", "[ ]")

        # check if the context curration is complete
        if self.curration_status == TaskState.Complete:
            return

        thinking = model_response.get("Thinking", "")
        logger.info(thinking)

        # load the plan
        self.plan = [PlanItem(p) for p in model_response.get("Plan")]

        # find the first pending item in the plan
        current_plan_item: PlanItem
        for item in self.plan:
            if PlanItem(item).state == TaskState.Pending:
                current_plan_item = item
                break

        # extract the ToolCalls from the plan item
        self.tool_calls = current_plan_item.tool_calls
        # if the model contains tool calls, process them
        if self.tool_calls:
            self.process_tool_calls()

    def process_tool_calls(self) -> str:
        tools_responses = []
        for tc in self.tool_calls:
            # skip completed tasks
            if tc.status == TaskState.COMPLETE:
                continue
            tool_path = f"{KONTXT_API_URL}/{tc['name']}{'/'.join(tc['args'])}"
            logger.debug(f"tool_path: {tool_path}")
            raw_response = requests.get(tool_path, timeout=60)

            logger.debug(f"Tool {tc['name']} Response: {raw_response.text}")
            if raw_response == "":
                return

            resp = json.loads(raw_response.text)
            tools_responses.append({tc["name"]: resp})

        # update the tool calls with the responses from the API
        if tools_responses:
            self.update_tool_calls = tools_responses

    def currate(self, user_message: str):
        """
        Currate the context

        This involves using the model to:
        * develop a plan
        * identify tools to use in the plan
        * execute those tools and update the context with their results

        The context is resubmitted to the model until the model indicates that it is done
        The model then summarizes the context so that it is as terse but complete as necessary for the LLM
        to handle the user's request
        """
        self.session = UserSession()
        self.user = user_message
