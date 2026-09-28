import asyncio
import json
import httpx
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.panel import Panel
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

app = typer.Typer(help="Chimera-X Brain Terminal Client")
console = Console()

API_URL = "http://localhost:8000"

style = Style.from_dict({
    'prompt': 'ansicyan bold',
})

async def fetch_status():
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{API_URL}/health")
            if res.status_code == 200:
                console.print(Panel("[bold green]Chimera-X Brain is Online[/bold green]\n" + str(res.json()), border_style="green"))
            else:
                console.print("[bold red]Backend returned an error.[/bold red]")
        except Exception as e:
            console.print(f"[bold red]Failed to connect to backend:[/bold red] {e}")
            console.print("Ensure 'uvicorn main:app' is running.")

async def fetch_models():
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{API_URL}/v1/models")
            if res.status_code == 200:
                models = res.json()
                table = Table(title="Available Models", border_style="cyan")
                table.add_column("Provider", style="magenta")
                table.add_column("Model Name", style="green")
                table.add_column("Capabilities")
                
                for m in models:
                    caps = []
                    if m.get("supports_vision"): caps.append("Vision")
                    if m.get("supports_tools"): caps.append("Tools")
                    caps_str = ", ".join(caps) if caps else "Text"
                    
                    # Litellm model format is often provider/model
                    provider = m.get("provider", "unknown").upper()
                    name = m.get("name", "unknown")
                    table.add_row(provider, name, caps_str)
                    
                console.print(table)
            else:
                console.print("[bold red]Failed to fetch models.[/bold red]")
        except Exception as e:
            console.print(f"[bold red]Failed to connect to backend:[/bold red] {e}")

async def chat_loop():
    console.print(Panel.fit("[bold cyan]Chimera-X Brain Terminal[/bold cyan]\nType [bold]/quit[/bold] to exit, [bold]/models[/bold] to list models, [bold]/clear[/bold] to wipe history.\nPress [bold]Esc + Enter[/bold] for multi-line submission if needed.", border_style="cyan"))
    
    session = PromptSession()
    messages = []
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        while True:
            try:
                # Use prompt toolkit for nice input
                user_input = await session.prompt_async("User ❯ ", style=style)
                user_input = user_input.strip()
                
                if not user_input:
                    continue
                if user_input.lower() in ["/quit", "/exit"]:
                    console.print("[yellow]Goodbye.[/yellow]")
                    break
                if user_input.lower() == "/clear":
                    messages = []
                    console.print("[green]Chat history cleared.[/green]")
                    continue
                if user_input.lower() == "/models":
                    await fetch_models()
                    continue
                
                messages.append({"role": "user", "content": user_input})
                
                req_data = {
                    "messages": messages,
                    "stream": True,
                    "model": "auto" # Let backend router decide
                }
                
                console.print("[cyan]Brain ❯ [/cyan]", end="")
                
                # We need to stream the SSE response
                full_response = ""
                async with client.stream("POST", f"{API_URL}/v1/chat/completions", json=req_data) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        console.print(f"\n[red]Error: {response.status_code} - {error_text.decode()}[/red]")
                        messages.pop() # Remove failed message
                        continue
                        
                    async for line in response.aiter_lines():
                        if line.startswith("data: ") and line != "data: [DONE]":
                            try:
                                data = json.loads(line[6:])
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        full_response += content
                                        # Print raw characters as they come, flush to terminal
                                        print(content, end="", flush=True)
                            except json.JSONDecodeError:
                                pass
                
                print() # Newline after response
                
                # Append assistant response to history
                messages.append({"role": "assistant", "content": full_response})
                
                # Display parsed markdown for better reading (optional, since we just streamed raw text)
                # But users usually prefer to see it streaming. 
                # We can print a nice divider
                console.print(f"[dim]─[/dim]" * 40)
                
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Exiting.[/yellow]")
                break
            except Exception as e:
                console.print(f"\n[red]Connection error: {e}[/red]")


@app.command()
def status():
    """Check the health of the Chimera-X Brain backend."""
    asyncio.run(fetch_status())

@app.command()
def models():
    """List all available routed models."""
    asyncio.run(fetch_models())

@app.command()
def chat():
    """Start an interactive chat session with the routing brain."""
    asyncio.run(chat_loop())

if __name__ == "__main__":
    app()
