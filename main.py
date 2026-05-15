# main.py - Big Fish Core Logic (720p Optimized Edition)
import subprocess, os, signal, time, sys, re, json
import tools, ui, jobs, audio 
from browser import AIStudioController, BrowserClosedError
from executor import execute_command
import prompts
import parser
import session

os.makedirs("projects", exist_ok=True)

def has_url(text): return bool(re.search(r'https?://\S+', text))
def get_url(controller):
    try: return controller.page.url
    except: return None
def get_tool_feedback(tool_name, tool_output): return tool_output

def estimate_tokens(history):
    history_text = "\n".join([f"{item['role']}: {item['content']}" for item in history])
    return (len(prompts.SYSTEM_PROMPT) + len(history_text)) // 4

def get_current_chrome_profile_dir():
    local_state_path = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\BigFish\Local State")
    
    try:
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.load(f)
        return local_state.get('profile', {}).get('last_used', 'Default')
    except Exception:
        return 'Default'

def main():
    ui.show_header()
    chrome_process, controller = None, None
    chat_history, current_session_file = [], None
    is_new_chat = True
    first_prompt = None
    carried_history_str = ""
    
    AI_CWD = os.getcwd()
    
    try:
        # THE FIX: Perfect 720p geometry (500x720 snapped to x=780)
        chrome_command = "start chrome --window-size=500,720 --window-position=780,0 --remote-debugging-port=9222 --user-data-dir=\"%LOCALAPPDATA%/Google/Chrome/User Data/BigFish\""
        chrome_process = subprocess.Popen(chrome_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        time.sleep(3)
        ui.show_status("Connecting to browser...")
        controller = AIStudioController()
        controller.connect() 
        ui.show_status("Agent is ready. Type /help for commands.")
        
        while True:
            try:
                user_input = ui.show_prompt(estimate_tokens(chat_history))
                is_image_prompt = False
                
                if user_input.startswith('/'):
                    cmd = user_input.split(' ')[0].lower()
                    if cmd == '/exit': break
                    elif cmd == '/help': ui.show_help(); continue
                    elif cmd == '/speech':
                        ui.show_status(f"🔊 Auto-Speech is now {'ON' if audio.toggle_speech() else 'OFF'} (Saved)."); continue
                    elif cmd == '/remind':
                        ui.show_status("📝 Injecting System Prompt Reminder into the chat...")
                        user_input = f"SYSTEM REMINDER - Please read and acknowledge your core operational instructions:\n\n{prompts.SYSTEM_PROMPT}"
                    elif cmd == '/jobs':
                        ui.show_bash_output("Background Jobs", jobs.list_background_jobs())
                        continue
                    elif cmd == '/kill':
                        parts = user_input.split()
                        if len(parts) > 1:
                            ui.show_status(jobs.stop_background_job(parts[1]))
                        else:
                            ui.show_error("Provide a job ID: /kill job_xxx")
                        continue
                    elif cmd == '/new':
                        carry_context = "--carry" in user_input.lower()
                        context_dump = ""
                        
                        if carry_context and chat_history:
                            context_dump = "\n".join([f"{item['role']}: {item['content']}" for item in chat_history])
                            carried_history_str = f"=== PREVIOUS CHAT CONTEXT ===\n{context_dump}\n===========================\n\n"
                        else:
                            carried_history_str = ""
                            AI_CWD = os.getcwd() 
                            
                        controller.start_new_chat()
                        is_new_chat, current_session_file, first_prompt = True, None, None
                        chat_history = []
                        
                        os.system('cls')
                        ui.show_header()
                        
                        if carry_context and context_dump:
                            ui.show_status(f"Started a fresh AI Studio chat (Context & CWD Carried Over: {AI_CWD}).")
                        else:
                            ui.show_status("Started a fresh AI Studio chat.")
                        continue
                    elif cmd == '/resume':
                        url, filename, preview, loaded_history, loaded_cwd, loaded_email, loaded_profile_dir = session.resume_session()
                        if url:
                            current_profile_dir = get_current_chrome_profile_dir()
                            
                            if loaded_profile_dir and loaded_profile_dir != current_profile_dir:
                                ui.show_status(f"🔄 Switching Chrome from {current_profile_dir} to {loaded_profile_dir} [{loaded_email}]...")
                                
                                if controller:
                                    try: controller.close()
                                    except: pass
                                if chrome_process:
                                    try: subprocess.run(f"taskkill /F /PID {chrome_process.pid} /T", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    except: pass
                                
                                time.sleep(1)
                                prof_flag = f'--profile-directory="{loaded_profile_dir}"'
                                
                                # THE FIX: Ensure 720p geometry applies during account restart
                                chrome_command = f"start chrome --window-size=500,720 --window-position=780,0 --remote-debugging-port=9222 --user-data-dir=\"%LOCALAPPDATA%/Google/Chrome/User Data/BigFish\" {prof_flag}"
                                chrome_process = subprocess.Popen(chrome_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                time.sleep(3)
                                controller = AIStudioController()
                                controller.connect()
                                ui.show_status("✔ Browser restarted with correct profile.")

                            ui.show_status("Loading chat URL in browser...")
                            controller.load_chat(url)
                            is_new_chat = False
                            current_session_file, first_prompt = filename, preview
                            chat_history = loaded_history
                            AI_CWD = loaded_cwd 
                            os.system('cls'); ui.show_header(); ui.show_status(f"Resumed session: {filename}")
                            if chat_history:
                                ui.reprint_history(chat_history)
                        else:
                            os.system('cls'); ui.show_header()
                        continue
                    elif cmd == '/clear': 
                        os.system('cls'); ui.show_header(); ui.show_status("Screen cleared.")
                        continue
                    elif cmd == '/m':
                        ui.show_status("📝 Multiline Mode Active. Type '/end' on an empty line to send.")
                        lines = []
                        while True:
                            line = input("  | ")
                            if line.strip() == '/end': break
                            lines.append(line)
                        user_input = "\n".join(lines)
                        if not user_input.strip(): continue
                    elif cmd == '/image':
                        is_image_prompt = True
                        user_input = user_input.replace('/image', '', 1).strip()
                        if not user_input: user_input = "Please analyze this image."
                    else: 
                        if cmd != '/remind':
                            ui.show_error("Unknown command.")
                            continue

                controller.configure_tools_for_prompt(enable_url_context=has_url(user_input))
                if is_image_prompt:
                    ui.show_status("🖼️  [IMG] Pasting image from OS clipboard to AI Studio...")
                    controller.paste_from_clipboard()

                if not first_prompt: first_prompt = user_input
                
                if is_new_chat:
                    base_prompt = f"{prompts.SYSTEM_PROMPT}\n\n{carried_history_str}=== USER REQUEST ===\n{user_input}"
                    is_new_chat = False
                    carried_history_str = "" 
                else:
                    base_prompt = user_input
                
                while True: 
                    try:
                        ui.show_status(f"Thinking... (CWD: {AI_CWD})")
                        start_time = time.time()
                        
                        turn_marker = f"[SYS_MARKER_{int(time.time()*1000)}]"
                        
                        raw_response = controller.send_prompt_and_get_response(base_prompt, turn_marker)
                        if raw_response is None: break 
                        
                        ui.show_status(f"⏱️ Response generated in {time.time() - start_time:.1f}s")
                        
                        current_url = controller.get_current_url()
                        actions = parser.smart_parse_ai_output(raw_response, turn_marker)
                        
                        if not actions or actions in["RATE_LIMIT", "PARSE_ERROR"]:
                            ui.show_error("AI format invalid or empty response. Forcing retry with full prompt reminder...")
                            base_prompt = f"{base_prompt}\n\n[SYSTEM ERROR: Your last output failed to parse. It is STRICTLY FORBIDDEN to output anything outside the <response> tags. You MUST use the <execute_tool> XML format. Here is a reminder of your core instructions:\n\n{prompts.SYSTEM_PROMPT}\n\nTry again.]"
                            continue
                        
                        if not isinstance(actions, list): actions = [actions]
                        
                        status = "continue"
                        has_talked = False
                        combined_feedback = ""
                        
                        for action_obj in actions:
                            status = action_obj.get("status", status)
                            
                            if "tools" in action_obj:
                                tools_to_run = action_obj.get("tools",[])
                            else:
                                tools_to_run = [action_obj] 
                            
                            for tool_call in tools_to_run:
                                tool = tool_call.get('tool', '').strip()
                                params = tool_call.get('parameters', {})
                                
                                if tool in['talk_to_user', 'sys_ask_user', 'sys_complete']:
                                    msg = params.get('message', params.get('question', params.get('summary', 'Task finished.')))
                                    ui.show_agent_reply(msg)
                                    chat_history.append({"role": "AI", "content": msg})
                                    has_talked = True
                                    if tool == 'sys_complete': status = "complete"
                                    continue 

                                raw_path = params.get('path') or params.get('file_path') or params.get('directory') or params.get('directory_path') or params.get('destination') or ''
                                abs_path = ""
                                if raw_path:
                                    if str(raw_path).startswith('~'):
                                        abs_path = os.path.expanduser(str(raw_path))
                                    elif os.path.isabs(str(raw_path)):
                                        abs_path = str(raw_path)
                                    else:
                                        abs_path = os.path.abspath(os.path.join(AI_CWD, str(raw_path)))

                                tool_output = ""
                                if tool == 'sys_change_directory':
                                    if os.path.isdir(abs_path):
                                        AI_CWD = abs_path
                                        tool_output = f"Success: Changed working directory to {AI_CWD}"
                                    else:
                                        tool_output = f"ERROR: Directory not found: {abs_path}"
                                    ui.show_status(tool_output)
                                elif tool == 'sys_run_command': 
                                    cmd_str = params.get('command', '').replace('&amp;', '&')
                                    tool_output = execute_command(cmd_str, cwd=AI_CWD)
                                    ui.show_bash_output(cmd_str, tool_output)
                                elif tool == 'sys_run_interactive': 
                                    tool_output = "ERROR: sys_run_interactive has been removed for stability. You MUST use sys_run_command for all shell executions."
                                    ui.show_error(tool_output)
                                elif tool == 'sys_read_file': 
                                    s_line = int(params.get('start_line')) if params.get('start_line') else None
                                    e_line = int(params.get('end_line')) if params.get('end_line') else None
                                    s_term = params.get('search_term') or params.get('search')
                                    surr = int(params.get('surrounding_lines')) if params.get('surrounding_lines') else 25
                                    r_all = str(params.get('read_all', '')).strip().lower() == 'true'
                                    tool_output = tools.read_file(abs_path, s_line, e_line, s_term, surr, read_all=r_all)
                                    ui.show_file_read(abs_path, tool_output)
                                elif tool == 'sys_write_file': 
                                    tool_output = tools.write_file(abs_path, params.get('content'))
                                    ui.show_file_write(abs_path, tool_output)
                                elif tool == 'sys_edit_file': 
                                    search_val = params.get('search') or params.get('search_text')
                                    replace_val = params.get('replace') or params.get('replace_text')
                                    s_line = int(params.get('start_line')) if params.get('start_line') else None
                                    e_line = int(params.get('end_line')) if params.get('end_line') else None
                                    tool_output = tools.edit_file(abs_path, search_val, replace_val, s_line, e_line)
                                    ui.show_file_edit(abs_path, tool_output)
                                elif tool == 'sys_create_dir':
                                    tool_output = tools.create_directory(abs_path)
                                    ui.show_file_write(abs_path, tool_output)
                                elif tool == 'sys_delete_file':
                                    tool_output = tools.delete_item(abs_path)
                                    ui.show_file_write(abs_path, tool_output)
                                elif tool == 'sys_rename_file':
                                    raw_new_path = params.get('new_path') or ''
                                    abs_new_path = ""
                                    if raw_new_path:
                                        if str(raw_new_path).startswith('~'):
                                            abs_new_path = os.path.expanduser(str(raw_new_path))
                                        elif os.path.isabs(str(raw_new_path)):
                                            abs_new_path = str(raw_new_path)
                                        else:
                                            abs_new_path = os.path.abspath(os.path.join(AI_CWD, str(raw_new_path)))
                                    tool_output = tools.rename_item(abs_path, abs_new_path)
                                    ui.show_file_edit(f"{abs_path} -> {abs_new_path}", tool_output)
                                elif tool == 'sys_list_dir': 
                                    target_dir = abs_path if abs_path else AI_CWD
                                    tool_output = tools.list_directory(target_dir)
                                    ui.show_bash_output(f"ls {target_dir}", tool_output)
                                elif tool == 'sys_search_text': 
                                    target_dir = abs_path if abs_path else AI_CWD
                                    tool_output = tools.grep_search(target_dir, params.get('search_text'))
                                    ui.show_bash_output(f"grep '{params.get('search_text')}' in {target_dir}", tool_output)
                                elif tool == 'sys_write_to_scratchpad': 
                                    tool_output = tools.write_to_scratchpad(params.get('content', ''), params.get('mode', 'a'))
                                    ui.show_status(tool_output)
                                elif tool == 'sys_start_background_job':
                                    cmd_str = params.get('command', '').replace('&amp;', '&')
                                    tool_output = jobs.start_background_job(cmd_str, cwd=AI_CWD)
                                    ui.show_bash_output(f"Start Background Job", tool_output)
                                elif tool == 'sys_stop_background_job':
                                    tool_output = jobs.stop_background_job(params.get('job_id'))
                                    ui.show_bash_output(f"Stop Job {params.get('job_id')}", tool_output)
                                elif tool == 'sys_list_background_jobs':
                                    tool_output = jobs.list_background_jobs()
                                    ui.show_bash_output("List Background Jobs", tool_output)
                                else: 
                                    tool_output = f"ERROR: Unknown tool '{tool}'."
                                    ui.show_error(tool_output)

                                feedback = get_tool_feedback(tool, tool_output)
                                chat_history.append({"role": "System", "content": f"Ran '{tool}'. Result:\n{feedback}"})
                                combined_feedback += f"Tool '{tool}' executed. Result:\n{feedback}\n\n"
                        
                        current_profile = controller.get_current_profile() if controller else "Unknown Profile"
                        current_profile_dir = get_current_chrome_profile_dir()
                        current_session_file = session.save_current_session(first_prompt, current_url, chat_history, AI_CWD, current_profile, current_profile_dir, current_session_file)
                        
                        if status == "complete" or not combined_feedback: break 
                        elif combined_feedback:
                            base_prompt = f"System Info: Current Working Directory is {AI_CWD}\n\nTool Results:\n{combined_feedback}"
                        
                    except KeyboardInterrupt:
                        ui.show_status("\n[bold red]🛑 Task aborted...[/bold red]")
                        break 
            except KeyboardInterrupt: break 
    except BrowserClosedError: ui.show_error("Browser closed.")
    finally:
        try: jobs.cleanup_all_jobs()
        except: pass
        current_profile = controller.get_current_profile() if controller else "Unknown Profile"
        current_profile_dir = get_current_chrome_profile_dir()
        current_url = get_url(controller) if controller else None
        current_session_file = session.save_current_session(first_prompt, current_url, chat_history, AI_CWD, current_profile, current_profile_dir, current_session_file)
        if current_session_file: ui.show_status(f"Session saved to {current_session_file}")
        if controller:
            try: controller.close()
            except: pass
        if chrome_process:
            try: subprocess.run(f"taskkill /F /PID {chrome_process.pid} /T", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except: pass
        ui.show_status("Cleanup complete.")

if __name__ == "__main__":
    main()
