# executor.py - Anti-Flood, Paginator & Hard Character Limit Edition (Windows Only)
import subprocess
import os
import sys
import threading
import collections
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

console = Console()

CMD_LOG_FILE = os.path.expanduser("~/gemini_local_agent/last_command_output.txt")

def _inject_sudo(command):
    """Strips sudo since Windows does not use it."""
    if command.strip().startswith("sudo "):
        return command.strip()[5:]
    return command
                else:
                    console.print("[bold red]❌ Incorrect password. Please try again.[/bold red]")
                    
        clean_cmd = command.strip()[5:]
        return f"echo '{pwd}' | sudo -S {clean_cmd}"
        
    return command

def execute_command(command, cwd=None):
    """Executes a shell command with a live, transient rolling window UI and dual-layer output pagination."""
    injected_command = _inject_sudo(command)
    
    full_output =[]
    rolling_lines = collections.deque(maxlen=15)
    is_timeout = [False]
    
    short_title = command[:50] + ("..." if len(command) > 50 else "")
    
    try:
        process = subprocess.Popen(
            injected_command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            cwd=cwd, 
            bufsize=1,
            universal_newlines=True
        )
        
        def timeout_handler():
            is_timeout[0] = True
            process.kill()
            
        timer = threading.Timer(120.0, timeout_handler)
        timer.start()
        
        with Live(Panel("Starting command...", title=f"⚡ Running: {short_title}", border_style="cyan"), refresh_per_second=10, transient=True) as live:
            for line in iter(process.stdout.readline, ''):
                full_output.append(line)
                rolling_lines.append(line.rstrip('\n'))
                
                display_text = "\n".join(rolling_lines) if rolling_lines else "..."
                live.update(Panel(display_text, title=f"⚡ Running: {short_title}", border_style="cyan"))
                
        process.wait()
        timer.cancel()
        
        result_str = "".join(full_output)
        lines = result_str.splitlines()
        total_lines = len(lines)
        total_chars = len(result_str)
        
        # THE FIX: Dual-Layer Paginator (Lines AND Characters)
        MAX_LINES = 100
        MAX_CHARS = 15000
        
        if total_lines > MAX_LINES or total_chars > MAX_CHARS:
            # Save the full massive output to the log file
            with open(CMD_LOG_FILE, 'w', encoding='utf-8', errors='replace') as f:
                f.write(result_str)
                
            # If it's a "normal" long output (many lines)
            if total_lines > MAX_LINES and (total_chars / max(1, total_lines)) < 500:
                truncated_lines = lines[-MAX_LINES:]
                start_idx = total_lines - MAX_LINES
                
                numbered_lines =[]
                for i, line in enumerate(truncated_lines):
                    actual_line_num = start_idx + i + 1
                    numbered_lines.append(f"{actual_line_num:4} | {line}")
                    
                trunc_str = "\n".join(numbered_lines)
                prefix = f"--- COMMAND OUTPUT TRUNCATED ---\nThe command produced {total_lines} lines of output.\nThe FULL output was automatically saved to: {CMD_LOG_FILE}\n(If you need to read the older logs to find an error, use sys_read_file on that path).\n\n--- LAST 100 LINES ---\n"
                result_str = prefix + trunc_str
                
            # If it's a massive jumbled single line (e.g. minified JS, giant JSON)
            else:
                trunc_str = result_str[-MAX_CHARS:]
                prefix = f"--- COMMAND OUTPUT TRUNCATED (SINGLE LINE/LARGE BLOB) ---\nThe command produced {total_chars} characters of output.\nThe FULL output was automatically saved to: {CMD_LOG_FILE}\n(If you need to read the full output, use sys_read_file on that path).\n\n--- LAST 15,000 CHARACTERS ---\n... "
                result_str = prefix + trunc_str
        
        if is_timeout[0]:
            return f"ERROR: Command timed out after 2 minutes.\nOutput before timeout:\n{result_str}"
            
        if process.returncode != 0:
            return f"ERROR (Exit Code {process.returncode}):\n{result_str}"
            
        return result_str
        
    except Exception as e:
        return f"PYTHON ERROR: Failed to execute command. {str(e)}"
