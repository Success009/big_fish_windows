# ui.py - The Advanced Interface Engine (Clean Layout Edition)
import os, sys, asyncio, logging
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.text import Text
from rich.markup import escape 
import audio  # THE FIX: Importing our newly separated audio engine

try:
    import nest_asyncio
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.application import run_in_terminal
except ImportError:
    print("Installing premium UI libraries 'prompt_toolkit' and 'nest_asyncio'...")
    os.system(f"{sys.executable} -m pip install prompt_toolkit nest_asyncio")
    import nest_asyncio
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.application import run_in_terminal

nest_asyncio.apply()
console = Console()
HISTFILE = os.path.expanduser("~/gemini_local_agent/.cli_history")
LAST_AGENT_REPLY = ""

class SlashCommandCompleter(Completer):
    def __init__(self):
        self.commands = ['/new', '/resume', '/sessions', '/clear', '/m', '/image', '/speech', '/exit', '/help', '/remind', '/jobs', '/kill']
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith('/') and ' ' not in text:
            for cmd in self.commands:
                if cmd.startswith(text.lower()):
                    yield Completion(cmd, start_position=-len(text))

bindings = KeyBindings()
@bindings.add('enter')
def _(event): event.current_buffer.validate_and_handle()
@bindings.add('escape', 'enter') 
def _(event): event.current_buffer.insert_text('\n')

@bindings.add('home')
@bindings.add('c-p')
def _(event):
    if audio.is_speaking():
        audio.stop_audio()
        run_in_terminal(lambda: console.print("[bold red]🔇 Speech Cancelled.[/bold red]"))
    else:
        global LAST_AGENT_REPLY
        if LAST_AGENT_REPLY:
            run_in_terminal(lambda: console.print("[bold cyan]🔊 Reading last reply from the top...[/bold cyan]"))
            audio.speak(LAST_AGENT_REPLY)

session = PromptSession(history=FileHistory(HISTFILE), completer=SlashCommandCompleter(), complete_while_typing=True, key_bindings=bindings, multiline=True)

def show_header():
    console.print(Panel.fit("[bold cyan]Big Fish CLI v7.6 (Modular Engine)[/bold cyan]\n[dim]Created by Success009 | Powered by Google Gemini[/dim]", border_style="cyan"))

def show_status(message): console.print(f"[bold yellow]{escape(message)}[/bold yellow]")

def show_prompt(token_count=0):
    state = "🔊 ON" if audio.SPEECH_ENABLED else "🔇 OFF"
    console.print(f"\n[dim][⚡ ~{token_count} tokens] [{state}] (Alt+Enter for new line | Home/Ctrl+P to Cancel/Replay)[/dim]")
    return session.prompt("Big Fish > ")

def show_agent_reply(content, auto_speak=True):
    global LAST_AGENT_REPLY
    LAST_AGENT_REPLY = content 
    console.print(Panel(Markdown(content), title="Big Fish AI", border_style="cyan", expand=False))
    if audio.SPEECH_ENABLED and auto_speak: 
        audio.speak(content)

def reprint_history(history):
    global LAST_AGENT_REPLY
    os.system('cls')
    show_header()
    for item in history[-10:]: 
        role, content = item.get("role"), item.get("content", "")
        if role == "User": print(f"\nBig Fish > {content}")
        elif role == "AI": show_agent_reply(content, auto_speak=False)
        elif role == "System":
            summary = content.split("Result: ")[-1]
            if "Ran 'sys_run_command'" in content: show_bash_output("Command from resumed session", summary)
            elif "Ran 'sys_read_file'" in content: show_file_read("File from resumed session", "Content loaded from memory...")

def show_bash_output(command, output):
    title = Text(f"🔧 Ran: {command}", style="bold magenta")
    if output:
        lines = output.splitlines()
        if len(lines) > 15:
            truncated_text = "\n".join(lines[-15:])
            safe_out = escape(truncated_text) + "\n\n[dim]... (output truncated for UI, AI received full context)[/dim]"
        else:
            safe_out = escape(output)
    else:
        safe_out = "[dim]No output[/dim]"
    console.print(Panel(safe_out, title=title, border_style="magenta", expand=False))

def show_file_read(path, content):
    console.print(Panel(Syntax(content, "python", theme="monokai", line_numbers=True), title=f"📄 Read: {path}", border_style="cyan"))

def show_file_write(path, result): 
    console.print(Panel(f"[green]✔[/green] {escape(result)}", title="File System", border_style="green"))

def show_file_edit(path, result): 
    console.print(Panel(f"[yellow]✎[/yellow] {escape(result)}", title="File System", border_style="yellow"))

def show_error(message): console.print(f"[bold red]ERROR: {escape(message)}[/bold red]")

def show_help():
    help_text = """
/new        - Start a fresh chat session
/new --carry- Carry context into a new account/chat
/resume     - Robust Menu to Load or Delete past sessions
/speech     - Toggle AI auto-voice ON/OFF (Saved)
/clear      - Clear terminal screen
/image      - Paste image from clipboard & send text
/m          - Enter multiline typing mode
/remind     - Send the core system prompt to the AI to re-align it
/jobs       - List all active background servers and processes
/kill [id]  - Manually terminate a background job (e.g. /kill job_1a2b3c)
/exit       - Quit the CLI

[Home] /[Ctrl+P] - Instantly cancel active speech or replay last message
    """
    console.print(Panel(help_text.strip(), title="Big Fish Commands", border_style="blue"))
