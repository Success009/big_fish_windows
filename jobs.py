# jobs.py - Background Process Manager
import os
import subprocess
import time
import uuid
import signal
from executor import _inject_sudo

LOG_DIR = os.path.expanduser("~/gemini_local_agent/logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Global registry to track running jobs
ACTIVE_JOBS = {}

def start_background_job(command, cwd=None):
    """Starts a command in the background, pipes output to a log, and checks for instant crashes."""
    job_id = f"job_{uuid.uuid4().hex[:6]}"
    log_path = os.path.join(LOG_DIR, f"{job_id}.log")
    
    injected_command = _inject_sudo(command)
    
    try:
        # Open the log file
        f = open(log_path, 'w', encoding='utf-8')
        f.write(f"--- STARTING BACKGROUND JOB: {command} ---\n")
        f.flush()
        
        # Popen runs the process in the background. 
        # os.setsid creates a process group so we can kill children (like Node servers) cleanly later.
        process = subprocess.Popen(
            injected_command,
            shell=True,
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd=cwd
        )
        
        # Wait 2 seconds. If a server instantly crashes (e.g., Port in use), we catch it immediately.
        time.sleep(2.0)
        
        if process.poll() is not None:
            f.close()
            with open(log_path, 'r', encoding='utf-8', errors='replace') as rf:
                log_content = rf.read()
            return f"ERROR: Job {job_id} crashed immediately (Exit Code {process.returncode}).\nLog Output:\n{log_content}"
        
        # Job survived the 2-second check; it is officially running.
        ACTIVE_JOBS[job_id] = {
            "process": process,
            "command": command,
            "log_path": log_path,
            "file_handle": f
        }
        return f"Success: Background job started and is running.\nJob ID: {job_id}\nLog File: {log_path}\n(Note: Use sys_read_file on this log path to monitor the server's live output)."
        
    except Exception as e:
        return f"ERROR starting background job: {str(e)}"

def stop_background_job(job_id):
    """Kills a background job and all its child processes."""
    if job_id not in ACTIVE_JOBS:
        return f"ERROR: Job {job_id} not found or already stopped."
        
    job = ACTIVE_JOBS[job_id]
    process = job["process"]
    
    try:
        subprocess.run(f"taskkill /F /T /PID {process.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        job["file_handle"].close()
        del ACTIVE_JOBS[job_id]
        return f"Successfully stopped background job: {job_id} ({job['command']})"
    except Exception as e:
        return f"ERROR stopping job: {str(e)}"

def list_background_jobs():
    """Lists all active background jobs, cleaning up any that died silently."""
    dead_jobs = []
    for jid, job in ACTIVE_JOBS.items():
        if job["process"].poll() is not None:
            job["file_handle"].close()
            dead_jobs.append(jid)
            
    for jid in dead_jobs:
        del ACTIVE_JOBS[jid]
        
    if not ACTIVE_JOBS:
        return "No active background jobs."
        
    output = ["--- ACTIVE BACKGROUND JOBS ---"]
    for jid, job in ACTIVE_JOBS.items():
        output.append(f"ID: {jid} | Command: {job['command']}\nLog: {job['log_path']}")
        
    return "\n\n".join(output)

def cleanup_all_jobs():
    """Failsafe to kill all jobs when the CLI exits."""
    for jid in list(ACTIVE_JOBS.keys()):
        stop_background_job(jid)
