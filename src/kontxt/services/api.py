import logging
from typing import Any, Dict

import fastapi
import uvicorn

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger.addHandler(logging.StreamHandler())

app = fastapi.FastAPI(title="Kontxt Service")


@app.get("/get-examples")
async def get_examples() -> Dict[str, str]:
    return {"message": "Hello World"}


@app.get("/tools")
async def get_tools() -> Dict[str, Any]:
    tools = {
        "directions": (
            "List of available tool collections and their tools.  "
            "Collections may be nested. To invoke a tool use the full "
            "path including collection names."
        ),
        "tools": [
            {
                "collection_name": "tollbox",
                "description": "tools to help select and use tools",
                "tools": [
                    {"get-examples": "Get examples for a tool", "args": ["tool_path"]},
                    {
                        "collection_name": "meta-arguments",
                        "description": (
                            "Meta arguments for tool invocation - "
                            "example: '&meta=use_cache' to use cached "
                            "parameters and results where available to "
                            "minimize passing data directly to and from "
                            "tools (uses file system)"
                        ),
                        "tools": [
                            {
                                "use-cache": (
                                    "Use cached parameters and results where available"
                                ),
                                "args": [],
                            }
                        ],
                    },
                ],
            },
            {
                "collection_name": "system-operations-tools",
                "description": "Tools for system operations. Examples: current system clock access",
                "tools": [
                    {
                        "get-current-date-time": "Get the current date and time",
                        "args": [],
                    },
                    {"get-system-status": "Get the current system status", "args": []},
                    {
                        "list-running-processes": "List all running processes",
                        "args": [],
                    },
                    {
                        "terminate-process": "Terminate a process",
                        "args": ["process-id"],
                    },
                    {"kill-process": "Kill a process", "args": ["process-id"]},
                ],
            },
            {
                "collection_name": "filesystem-tools",
                "description": "Tools for filesystem operations. Examples: read/write files, list directories",
                "tools": [
                    {"read-file": "Read contents of a file", "args": ["file_path"]},
                    {
                        "write-file": "Write content to a file",
                        "args": ["file-path", "content"],
                    },
                    {
                        "list-directory": "List files in a directory",
                        "args": ["directory-path"],
                    },
                    {
                        "create-directory": "Create a new directory",
                        "args": ["directory-path"],
                    },
                    {"delete-file": "Delete a file", "args": ["file_path"]},
                    {
                        "copy-file": "Copy a file to a new location",
                        "args": ["source-path", "dest-path"],
                    },
                    {
                        "move-file": "Move or rename a file",
                        "args": ["source-path", "dest-path"],
                    },
                ],
            },
            {
                "collection_name": "text_editing_tools",
                "description": (
                    "Tools for editing and manipulating text. "
                    "Examples: text summarization, grammar correction"
                ),
                "tools": [
                    {"summarize_text": "Summarize text content", "args": ["text"]},
                    {"grammar_check": "Check and correct grammar", "args": ["text"]},
                    {"word_count": "Count words in text", "args": ["text"]},
                    {
                        "find_replace": "Find and replace text patterns",
                        "args": ["text", "search_pattern", "replacement"],
                    },
                    {
                        "extract_keywords": "Extract keywords from text",
                        "args": ["text"],
                    },
                ],
            },
            {
                "collection_name": "math_tools",
                "description": "Tools for mathematical computations. Examples: basic arithmetic, algebra, calculus",
                "tools": [
                    {
                        "basic_arithmetic": "Perform basic arithmetic operations",
                        "args": ["operation", "operand1", "operand2"],
                    },
                    {
                        "solve_equation": "Solve algebraic equations",
                        "args": ["equation"],
                    },
                    {
                        "matrix_operations": "Perform matrix operations",
                        "args": ["operation", "matrix1", "matrix2"],
                    },
                    {
                        "statistical_analysis": "Compute statistical measures",
                        "args": ["data", "measure"],
                    },
                    {
                        "numerical_integration": "Perform numerical integration",
                        "args": ["function", "limits"],
                    },
                ],
            },
            {
                "collection_name": "data_processing_tools",
                "description": "Tools for data processing and analysis. Examples: data cleaning, statistical analysis",
                "tools": [
                    {
                        "clean_data": "Remove duplicates and handle missing values",
                        "args": ["dataset"],
                    },
                    {
                        "filter_data": "Filter data by conditions",
                        "args": ["dataset", "filter_criteria"],
                    },
                    {
                        "aggregate_data": "Aggregate data by groups",
                        "args": ["dataset", "group_by"],
                    },
                    {
                        "join_datasets": "Join multiple datasets",
                        "args": ["dataset1", "dataset2", "join_key"],
                    },
                    {
                        "pivot_table": "Create pivot tables from data",
                        "args": ["dataset", "rows", "columns", "values"],
                    },
                ],
            },
            {
                "collection_name": "data_visualization_tools",
                "description": "Tools for data visualization. Examples: plotting graphs, creating charts",
                "tools": [
                    {
                        "plot_line_chart": "Create line charts",
                        "args": ["data", "x_label", "y_label"],
                    },
                    {
                        "plot_bar_chart": "Create bar charts",
                        "args": ["categories", "values"],
                    },
                    {
                        "plot_scatter": "Create scatter plots",
                        "args": ["x_data", "y_data"],
                    },
                    {"plot_histogram": "Create histograms", "args": ["data", "bins"]},
                    {
                        "create_heatmap": "Create heatmap visualizations",
                        "args": ["matrix"],
                    },
                ],
            },
            {
                "collection_name": "web_tools",
                "description": "Tools for web operations. Examples: web scraping, API interactions",
                "tools": [
                    {"fetch_url": "Fetch content from a URL", "args": ["url"]},
                    {
                        "parse_html": "Parse and extract data from HTML",
                        "args": ["html_content", "selector"],
                    },
                    {
                        "scrape_webpage": "Scrape data from a webpage",
                        "args": ["url", "selectors"],
                    },
                    {
                        "make_api_call": "Make an HTTP API call",
                        "args": ["url", "method", "headers", "body"],
                    },
                    {"validate_url": "Validate and normalize URLs", "args": ["url"]},
                ],
            },
        ],
    }
    return tools


if __name__ == "__main__":
    # Bind to all interfaces so the service is reachable from other containers
    uvicorn.run(app, host="0.0.0.0", port=8000)
