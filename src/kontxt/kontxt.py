import json
import logging
from typing import Dict, List
from uuid import uuid1

import requests

from kontxt.tool_call import ToolCall
from kontxt.user_session import UserSession

MAX_CONTEXT_TOKENS = 4096
MODEL = "gpt-oss"
OLLAMA_API_URL = "http://localhost:11435/api/generate"
KONTXT_API_URL = "http://localhost:8001/"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Kontxt:
    _context: Dict[str, UserSession] = {}
    _key: str = ""

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

You are a Context Orchestrator AI named Kontxt.
Your job is to curate relevant context and tool calls to help
the LLM effectively implement user requests with high accuracy and efficiency.
Your task is to currate the most complete but terse context necessary to help the LLM
resolve the users request.  The context shall not exceed {MAX_CONTEXT_TOKENS} tokens.
Respond only in JSON format, following this schema:

### Response Schema

```
{{
"User": string,
"Plan": [
    {{  "status": string,
        "description": string,
        "tool_calls": [{{'name': string, 'args': list[string], "results": list[string]}},
                    ...
                    ]}},
        ],
"Context": [string],
"CurrationStatus": string
}}
```

_whereas_:
    * User is the original user prompt / request / message
    * Plan is your step-by-step plan to currate the necessary information to provide an LLM to
        fulfill the user request.  Each plan item starts with a status:
        * Status:
            * "[ ]": Pending; default starting status for each task
            * "[✔️]": Complete; task is completed and successful
            * "[X]": Failed; task was attempted and failed - may need to be re-considered
        * "tool_calls" is a list of tool calls needed to implement or provide information to
            complete the plan step.
            * "name": The name of the tool call.
            * "args": A list of arguments for the tool call.
                * If no args are needed, return an empty list.
            * "results": A list of results produced by the tool call.
                * If no results are needed, return an empty list.
        * DECISION:  Based on information gathered, extend the plan if needed.
            to produce information you will use in currating context for the LLM to use
            in next response to the user. If no tool calls are needed, return an empty list.
        * DECISION:  Based on information gathered, extend the plan if needed.

        [INSIGHT] the plan may be updated and decisions can change throughout the process,
        but the plan should retain completed tasks to inform the context curation process
        [END INSIGHT]
    * Context is the context work-in-progress
    * CurationStatus: the status of your plan.  Should start with a pending status ("[ ]")
        * [CRITICAL] Mark the CurationStatus complete ("[✔️]") when the Context is ready for
            the LLM to consume
        * Curation Status Values:
            * "[ ]": Pending; default starting status for the new context
            * "[✔️]": Complete; your curration of the context is complete and it is
             ready for the LLM to consume

### tool_calls

[INSIGHT] There is no 'python' or other scripting tool.  Use ToolCalls and registered tools
[INSIGHT] To find relevant tools, use the ToolCalls to get a list of available tools.
[INSIGHT] The results of tool calls will be added to the context for future responses.

Example: Get the tool collections index:
```
{{ "ToolCalls": [
    {{"name": "tools", "args": []}}
    ]
}}
```

[HINT] Use this if you need to find the right tool

[INSIGHT] After getting the list of tools, you can call other tools as needed.

Example: Get the tools from the filesystem-tools collection:
```
{{ "ToolCalls": [
    {{"name": "tools", "args": ["filesystem-tools"]}}
    ]
}}
```

[INSIGHT] Use tools to gather information needed to fulfill user requests.
If no tools are needed, return an empty list for ToolCalls.
[END INSIGHT]

### Context Curration

The context should contain only relevant information for the LLM to produce a
high-quality result.  It does not need to contain the final final response, but
may contain facts and data that the LLM will synthesize into a final response.

The context shall not exceed {MAX_CONTEXT_TOKENS} tokens.  If necessary, summarize
portions of the context to minimize the number of tokens.

Use tool_calls to perform filtering, summarization, off-loading of content
to temporary files for your purposes and to reduce the number of tokens and
relevance of data within the context.

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

        model_response_raw = response_json.get("response", "")
        if model_response_raw == "":
            return
        model_response = json.loads(model_response_raw)

        # thinking = model_response.get("Thinking", "")

        # add the plan to the context
        self.plan = model_response.get("Plan", [])

        # extract the ToolCalls from the model response and add them to context
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
        self.session = UserSession()
        self.user = user_message
