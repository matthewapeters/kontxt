from typing import Any, Dict, List
import json
import logging

from pydantic import BaseModel
import requests
from uuid import uuid1

from kontxt.task_state import TaskState


MODEL = "gpt-oss"
OLLAMA_API_URL = "http://localhost:11435/api/generate"
KONTXT_API_URL = "http://localhost:8001/"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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


class PlanItem(BaseModel):
    state: TaskState = TaskState.PENDING
    task: str
    tool_calls: List[ToolCall] = []

    def to_string(self) -> str:
        tool_call_results = "\n".join([t.to_string() for t in self.tool_calls])
        return f"""{self.plan_state} {self.task}{toll_call_results}"""


class UserSession(BaseModel):
    plan: List[PlanItem]
    user: str
    context: List[str] = []


class Kontxt:
    _context:Dict[str, UserSession] = {}
    _key: str = ""

    @property
    def session(self)->UserSession:
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

    def query_ollama(self):
        prompt: str = f"""
# Agent Directive

[CRITICAL] Follow these instructions systematically

## System

You are a Context Orchestrator AI named Kontxt.
Your job is to curate relevant context and tool calls to help
the LLM effectively implement user requests with high accuracy and efficiency.
Respond only in JSON format, following this schema:

{{
"ToolCalls": [{{'name': string, 'args': list[string]}}],
"Plan": [
"[✔️] Step 1 which is marked because it is completed",
"[ ] Step 2 is the nexte step to do, and will be marked completed when the context contains the evidence that the step is completed",
"DECISION:  Based on information gathered, extend the plan if needed.",
"..."
],
"Context": string,
"Thinking": string,
"User": string
}}

_whereas_:
    * ToolCalls is a list of tool calls you recommend the framework to make
        to produce information you will use in currating context for the LLM to use
        in next response to the user. If no tool calls are needed, return an empty list.
    * Plan is your step-by-step plan to currate the necessary information to provide an LLM to fulfill the user request.
        Each step should be marked as completed "[✔️]" when the context contains evidence that the step has been accomplished.
        DECISION:  Based on information gathered, extend the plan if needed.
        [INSIGHT] the plan may be updated and decisions can change throughout the process,
        but the plan should retain completed tasks to inform the context curation process
        [END INSIGHT]
    * Context is the curated context you recommend the framework to provide to the LLM
    * User is the original user message.

[INSIGHT] There is no 'python' or other scripting tool.  Use ToolCalls and registered tools
[INSIGHT] To find relevant tools, use the ToolCalls to get a list of available tools.
[INSIGHT] The results of tool calls will be added to the context for future responses.

Example: Get the tool collections index:
{{ "ToolCalls": [
    {{"name": "tools", "args": []}}
    ]
}}
[HINT] Use this if you need to find the right tool


[INSIGHT] After getting the list of tools, you can call other tools as needed.

Example: Get the tools from the filesystem-tools collection:
{{ "ToolCalls": [
    {{"name": "tools", "args": ["filesystem-tools"]}}
    ]
}}

[INSIGHT] Use tools to gather information needed to fulfill user requests.
If no tools are needed, return an empty list for ToolCalls.
[END INSIGHT]

## Plan
{self.plan_str}

## Context
{self.context_str}

## User
{self.user}
"""
        logger.debug(f"Prompt sent to Ollama: {prompt}")
        response_json = requests.post(
            OLLAMA_API_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        ).json()
        logger.debug(f"Ollama Response JSON: {response_json}")

        result = ""

        model_response_raw = response_json.get("response", "")
        if model_response_raw == "":
            return
        model_response = json.loads(model_response_raw)

        # thinking = model_response.get("Thinking", "")

        # add the plan to the context
        self.plan = model_response.get("Plan", [])

        # extract the ToolCalls from the model response and add them to the context
        self.tool_calls = [ToolCall(**o) for o in model_response.get("ToolCalls", [])]
        # if the model contains tool calls, process them
        if self.tool_calls:
            self.process_tool_calls()

    def process_tool_calls(self) -> str:
        tools_responses = []
        for tc in self.tool_calls:
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
        self.session = Session()
        self.user = user_message
