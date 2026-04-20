"""Copilot CLI for the Consequence Platform."""

import sys
import json
import os
import asyncio
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from openai import AsyncOpenAI

from copilot_cli import api_client

console = Console()

# We configure the OpenAI client to point to the local Ollama instance (or whichever is configured)
AGENT_BASE_URL = os.getenv("AGENT_BASE_URL", "http://localhost:11434/v1")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "ollama")
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemma4") # Wait, gemma4 might not support tools out of the box in Ollama perfectly, but we'll try!

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "start_evaluation",
            "description": "Start a new evaluation job on the consequence platform.",
            "parameters": {
                "type": "object",
                "properties": {
                    "suite": {
                        "type": "string",
                        "description": "The name of the evaluation suite to run (e.g., 'calculator')."
                    },
                    "agent_name": {
                        "type": "string",
                        "description": "The name of the agent runner to use (e.g., 'default'). Defaults to 'default'."
                    },
                    "model": {
                        "type": "string",
                        "description": "The model to evaluate (e.g., 'gemma4'). Defaults to 'gemma4'."
                    },
                    "llm_judge": {
                        "type": "boolean",
                        "description": "Whether to use an LLM for judging."
                    }
                },
                "required": ["suite"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_job_status",
            "description": "Check the status of a specific single evaluation job. You MUST have a specific UUID job_id to use this.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "The UUID of the job."
                    }
                },
                "required": ["job_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_jobs",
            "description": "List all active or past evaluation jobs and their statuses. Use this when the user asks for all jobs or when no specific job ID is provided.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_all_jobs",
            "description": "Delete all job history and clear the database.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

async def execute_tool(name: str, args: dict[str, Any]) -> str:
    """Execute the chosen tool against the REST API."""
    console.print(f"[dim info]Executing action: {name}({args})[/dim info]")
    if name == "start_evaluation":
        suite = args.get("suite", "calculator")
        agent_name = args.get("agent_name", "default")
        model = args.get("model", "gemma4")
        llm_judge = args.get("llm_judge", False)
        result = api_client.start_evaluation(suite, agent_name, model, llm_judge)
        return json.dumps(result)
        
    elif name == "check_job_status":
        job_id = args.get("job_id", "")
        result = api_client.check_job_status(job_id)
        
        # Pretty print the payload instantly for the user so they don't have to wait for the LLM!
        console.print(f"\n[bold magenta]--- SYSTEM LOCAL API FETCH: {job_id} ---[/bold magenta]")
        try:
            from rich.json import JSON
            console.print(JSON.from_data(result))
        except:
            console.print(result)
        console.print("[bold magenta]------------------------------------------------[/bold magenta]\n")
        
        return json.dumps(result)
        
    elif name == "list_jobs":
        result = api_client.list_jobs()
        # To avoid blowing up the context window, we might want to truncate
        job_ids = list(result.keys())
        summary = {jid: result[jid].get("status", "UNKNOWN") for jid in job_ids}
        return json.dumps(summary)
        
    elif name == "delete_all_jobs":
        result = api_client.delete_all_jobs()
        return json.dumps(result)
        
    return '{"error": "Unknown function"}'


async def main_loop():
    console.print("[bold green]Welcome to the Consequence Copilot CLI![/bold green]")
    console.print("I am your AI assistant for the Consequence evaluation platform.")
    console.print(f"Using Model: [bold blue]{AGENT_MODEL}[/bold blue] at [blue]{AGENT_BASE_URL}[/blue]")
    console.print("Type 'exit' or 'quit' to leave.\n")

    session = PromptSession()
    client = AsyncOpenAI(base_url=AGENT_BASE_URL, api_key=AGENT_API_KEY)
    
    messages = [
        {"role": "system", "content": "You are the Copilot for the 'consequence' AI Agent Evaluation Platform. "
         "Your goal is to help users manage evaluations. Help them run suites, check statuses, and list jobs. "
         "You MUST ALWAYS use the provided tools to interact with the backend API on behalf of the user. "
         "NEVER guess, block, hallucinate, or generate mocked JSON data. "
         "If the user asks for a list, you MUST call the list_jobs tool. Do NOT answer the question directly without calling a tool first. "
         "Keep your English responses very concise and focus only on providing the factual job details and statuses returned by the tools."}
    ]

    while True:
        try:
            # Get input
            user_input = await session.prompt_async(HTML("<ansibrightcyan>copilot></ansibrightcyan> "))
            
            if not user_input.strip():
                continue
                
            if user_input.lower() in ("exit", "quit"):
                console.print("[yellow]Goodbye![/yellow]")
                break

            messages.append({"role": "user", "content": user_input})

            with console.status("[cyan]Thinking..."):
                response = await client.chat.completions.create(
                    model=AGENT_MODEL,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto"
                )

            message = response.choices[0].message
            messages.append(message)
            
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)
                    
                    tool_result = await execute_tool(func_name, func_args)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": tool_result
                    })
                
                with console.status("[cyan]Synthesizing response..."):
                    second_response = await client.chat.completions.create(
                        model=AGENT_MODEL,
                        messages=messages
                    )
                
                final_msg = second_response.choices[0].message.content
                messages.append({"role": "assistant", "content": final_msg})
                console.print(f"[green]{final_msg}[/green]")
            else:
                # FALLBACK: Local models (e.g., Llama 1B) often hallucinate tool calls into text
                import re
                try:
                    content = message.content or ""
                    # Grab JSON block if it exists
                    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                    raw_json = match.group(1) if match else content.strip()
                    
                    if raw_json.startswith("{") and raw_json.endswith("}"):
                        data = json.loads(raw_json)
                        if "name" in data and ("parameters" in data or "arguments" in data):
                            name_str = data.get("name", "")
                            
                            # Clean up dirty LLM function names
                            func_name = None
                            if "start_eval" in name_str: func_name = "start_evaluation"
                            elif "check_job" in name_str or "status" in name_str: func_name = "check_job_status"
                            elif "list_jobs" in name_str: func_name = "list_jobs"
                            elif "delete" in name_str: func_name = "delete_all_jobs"
                            else: func_name = name_str
                            
                            params = data.get("parameters", data.get("arguments", {}))
                            
                            # Clean up dirty array strings (e.g. "['1234']")
                            for k, v in params.items():
                                if isinstance(v, str) and v.startswith("['") and v.endswith("']"):
                                    params[k] = v[2:-2]
                                    
                            console.print("[dim yellow]Fallback parsed malformed tool call...[/dim yellow]")
                            tool_result = await execute_tool(func_name, params)
                            console.print(f"[green]{tool_result}[/green]")
                            continue
                except Exception:
                    pass
                
                console.print(f"[green]{message.content}[/green]")

        except EOFError:
            break
        except KeyboardInterrupt:
            continue
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def main():
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
