import logging
import tkinter as tk
from tkinter import messagebox, scrolledtext

import requests

from kontxt.kontxt import Kontxt

MODEL = "gpt-oss"
OLLAMA_API_URL = "http://localhost:11435/api/generate"
KONTXT_API_URL = "http://localhost:8001/"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ChatApp:
    context = Kontxt()
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

    def send_message(self):
        message = self.entry_field.get("1.0", tk.END).strip()
        logger.debug(f"User Message: {message}")
        if message:
            self.context.curate(message)
            try:
                self.context_area.delete("1.0", tk.END)

                self.context_area.insert(
                    tk.END,
                    self.context.context_str,
                )

                self.text_area.insert(tk.END, f"{MODEL}: {self.context.summary}\n\n")

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
