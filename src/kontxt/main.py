from typing import Any, Dict, List
import logging
import tkinter as tk
import requests
import json
from tkinter import messagebox, scrolledtext

from kontxt.json_logger import JsonFormatter

MODEL = "gpt-oss"
OLLAMA_API_URL = "http://localhost:11435/api/generate"
KONTXT_API_URL = "http://localhost:8001/"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)


class ChatApp:
    CONTEXT = []
    n = 21  # Number of previous exchanges to retain in context - multiples of 3

    def __init__(self, root):
        self.root = root
        self.root.title("Chat with Ollama")
        self.root.rowconfigure(4, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)

        self.label = tk.Label(self.root, text="Chat Interface")
        self.context_label = tk.Label(self.root, text=f"Context ({self.n} entries):")
        self.context_label.grid(row=0, column=0)
        self.response_label = tk.Label(self.root, text="Response:")
        self.response_label.grid(row=0, column=1)
        self.context_area = scrolledtext.ScrolledText(self.root)
        self.context_area.grid(row=1, column=0, sticky="nsew")
        self.text_area = scrolledtext.ScrolledText(self.root)
        self.text_area.grid(row=1, column=1, sticky="nsew")
        self.input_label = tk.Label(self.root, text="Your Message:")
        self.input_label.grid(row=2, column=0, columnspan=2)
        self.entry_field = tk.Text(self.root, width=50, height=3)
        self.entry_field.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.button = tk.Button(self.root, text="Send", command=self.send_message)
        self.button.grid(row=4, column=0, columnspan=2)


    def process_tool_calls(self, tool_calls: List[Dict[str, Any]])->str:
        tools_responses=[]
        for tc in tool_calls:
            tool_path = f"{KONTXT_API_URL}/{tc['name']}{'/'.join(tc['args'])}" 
            logger.debug(f"tool_path: {tool_path}")
            raw_response = requests.get(
                tool_path,
                timeout=60)
            
            logger.debug(f"Tool {tc['name']} Response: {raw_response.text}")
            if raw_response == "":
                return

            resp = json.loads(raw_response.text)
            tools_responses.append({tc['name']: resp})
        return json.dumps(tools_responses, indent=2)


    def query_ollama(self):
                ctxt = "\n".join(self.CONTEXT)
                prompt: str = f"""System: You are a Context Orchestrator AI named Kontxt.
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

whereas:
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


Context: {ctxt}

User: {message}
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
            except Exception as e:
                  logger.exception(e, stack_info=True)
        else:
              logger.debug("no message")


    def send_message(self):
        message = self.entry_field.get("1.0", tk.END).strip()
        logger.debug(f"User Message: {message}")
        thinking = ""
        response = ""
        if message:
            try:
                response_json = self.query_ollama(message)
                logger.debug(f"Ollama Response JSON: {response_json}")

                result=""
                self.context_area.delete("1.0", tk.END)

                model_response_raw = response_json.get("response", "")
                if model_response_raw == "":
                    return
                model_response = json.loads(model_response_raw)
                tool_calls = model_response.get("ToolCalls", [])
                self.CONTEXT.append(f"Tool Results: {self.process_tool_calls(tool_calls)}")
                
                # thinking = model_response.get("Thinking", "")
                plan = model_response.get("Plan",[])
                logger.debug(f"Plan: {plan}")

                plan_str = json.dumps(plan)

                # Implement logic to retain the running window as context
                logger.debug(f"Updating context with message: {message}, plan: {plan_str}, response: {response}")
                self.CONTEXT.append(f"Plan: {plan_str}")
                self.CONTEXT.append(f"User: {message}")
                self.CONTEXT = self.CONTEXT[self.n * -1 :]  # Keep only the last n entries

                self.context_area.insert(
                    tk.END,
                    "\n".join(self.CONTEXT),
                )
                self.text_area.insert(tk.END, f"{MODEL}: {result}\n\n")

            except requests.exceptions.ConnectionError:
                logger.exception("Connection error")
                messagebox.showerror(
                    "Error",
                    f"Failed to connect to Ollama API at {OLLAMA_API_URL}.\n"
                    "Make sure the docker-compose services are running:\n"
                    "  cd docker_compose && docker-compose up -d",
                )
            except Exception as e:
                logger.exception(e)
                messagebox.showerror("Error", "Failed to send message: {}".format(e))
            finally:
                self.entry_field.delete("1.0", tk.END)


root = tk.Tk()
app = ChatApp(root)
root.mainloop()
