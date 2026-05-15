# tools.py - The Capabilities Engine (Full Filesystem Edition)
import os
import glob
import re
import shutil

SCRATCHPAD_FILE = os.path.expanduser("~/gemini_local_agent/scratchpad.txt")

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

def read_file(path, start_line=None, end_line=None, search_term=None, surrounding_lines=25, read_all=False):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            
        total_lines = len(lines)
        if total_lines == 0:
            return f"--- {path} is empty ---"

        if search_term:
            match_idx = -1
            for i, line in enumerate(lines):
                if search_term in line:
                    match_idx = i
                    break
            if match_idx == -1:
                return f"ERROR: The search term '{search_term}' was not found in {path}."
            
            s_line = max(1, match_idx + 1 - surrounding_lines)
            e_line = min(total_lines, match_idx + 1 + surrounding_lines)
            
        else:
            if read_all:
                s_line = 1
                e_line = total_lines
            elif start_line is not None and end_line is None:
                s_line = max(1, int(start_line))
                e_line = min(total_lines, s_line + 500)
            elif end_line is not None and start_line is None:
                e_line = min(total_lines, int(end_line))
                s_line = max(1, e_line - 500)
            elif start_line is not None and end_line is not None:
                s_line = max(1, int(start_line))
                e_line = min(total_lines, int(end_line))
            else:
                s_line = 1
                e_line = min(total_lines, 500)
                if total_lines > 500:
                    warning = f"\n\n[SYSTEM WARNING: File has {total_lines} lines. You only saw lines 1-500. Use <start_line> and <end_line> to read more, or set <read_all>true</read_all> to load everything.]"

        output_lines =[]
        for i in range(s_line - 1, e_line):
            output_lines.append(f"{i+1:4} | {lines[i]}")
            
        content = "".join(output_lines)
        res = f"--- Reading lines {s_line} to {e_line} of {total_lines} in {path} ---\n{content}"
        
        if 'warning' in locals():
            res += warning
            
        return res
        
    except FileNotFoundError:
        return f"ERROR: File not found at {path}"
    except Exception as e:
        return f"ERROR: Could not read file. {str(e)}"

def write_file(path, content):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"ERROR: Could not write file. {str(e)}"

def edit_file(path, search_text=None, replace_text=None, start_line=None, end_line=None):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            original_content = f.read()
            lines = original_content.splitlines(True)
            
        edit_start_line_idx = 0
        replace_str = replace_text if replace_text else ""
            
        if search_text is not None and replace_text is not None:
            if search_text in original_content:
                exact_match = search_text
            else:
                normalized_search = re.sub(r'\s+', ' ', search_text.strip())
                escaped_search = re.escape(normalized_search)
                fuzzy_pattern = escaped_search.replace(r'\ ', r'\s*')
                
                matches = list(re.finditer(fuzzy_pattern, original_content))
                
                if not matches:
                    return f"ERROR: No changes made. The text '{search_text[:50]}...' was not found in {path}."
                elif len(matches) > 1:
                    return f"ERROR: The search block matches {len(matches)} places. Please provide a more unique <search> block."
                else:
                    exact_match = matches[0].group(0)
            
            char_idx = original_content.find(exact_match)
            edit_start_line_idx = original_content.count('\n', 0, char_idx)
            new_content = original_content.replace(exact_match, replace_str, 1)
                    
        elif start_line is not None and end_line is not None:
            s_idx = max(0, int(start_line) - 1)
            e_idx = min(len(lines), int(end_line))
            edit_start_line_idx = s_idx
            
            if replace_str and not replace_str.endswith('\n'):
                replace_str += '\n'
                
            lines[s_idx:e_idx] = [replace_str]
            new_content = "".join(lines)
        else:
            return "ERROR: You must provide either <search>&<replace>, OR <start_line>,<end_line>&<replace>."
            
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(new_content)
            
        rep_line_count = len(replace_str.splitlines())
        if rep_line_count <= 3:
            new_lines = new_content.splitlines(True)
            ctx_start = max(0, edit_start_line_idx - 20)
            ctx_end = min(len(new_lines), edit_start_line_idx + rep_line_count + 20)
            
            ctx_out =[]
            for i in range(ctx_start, ctx_end):
                ctx_out.append(f"{i+1:4} | {new_lines[i]}")
                
            ctx_str = "".join(ctx_out)
            return f"Successfully edited {path}.\n--- Context Around Your Edit ---\n{ctx_str}"
        else:
            return f"Successfully edited large block in {path}."
            
    except Exception as e:
        return f"ERROR: Could not edit file. {str(e)}"

# --- NEW TOOLS ---
def create_directory(path):
    """Creates a new directory (and any necessary parent directories)."""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Successfully created directory: {path}"
    except Exception as e:
        return f"ERROR: Could not create directory. {str(e)}"

def delete_item(path):
    """Safely deletes a file or an entire directory tree."""
    try:
        if not os.path.exists(path):
            return f"ERROR: Item not found at {path}"
        if os.path.isdir(path):
            shutil.rmtree(path)
            return f"Successfully deleted directory: {path}"
        else:
            os.remove(path)
            return f"Successfully deleted file: {path}"
    except Exception as e:
        return f"ERROR: Could not delete {path}. {str(e)}"

def rename_item(old_path, new_path):
    """Renames or moves a file or directory."""
    try:
        if not os.path.exists(old_path):
            return f"ERROR: Item not found at {old_path}"
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        os.rename(old_path, new_path)
        return f"Successfully renamed {old_path} to {new_path}"
    except Exception as e:
        return f"ERROR: Could not rename. {str(e)}"
# -----------------

def list_directory(path):
    try:
        if not os.path.exists(path):
            return f"ERROR: Directory not found at {path}"
            
        entries = os.listdir(path)
        if not entries: 
            return "The directory is empty."
            
        output =[]
        for entry in sorted(entries):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                output.append(f"[DIR]  {entry}/")
            elif os.path.isfile(full_path):
                size_bytes = os.path.getsize(full_path)
                size_str = format_size(size_bytes)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)
                    output.append(f"[FILE] {entry} - {line_count} lines ({size_str})")
                except UnicodeDecodeError:
                    output.append(f"[FILE] {entry} - Binary/Media ({size_str})")
                except Exception:
                    output.append(f"[FILE] {entry} - Unknown ({size_str})")
            else:
                output.append(f"[OTHER] {entry}")
                
        return "\n".join(output)
    except Exception as e:
        return f"ERROR: Could not list directory. {str(e)}"

def grep_search(directory, search_text):
    try:
        results = list()
        for filepath in glob.glob(os.path.join(directory, '**', '*'), recursive=True):
            if os.path.isfile(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f):
                            if search_text in line:
                                results.append(f"{filepath}:{i+1}:{line.strip()}")
                except Exception:
                    continue
        return "\n".join(results) if results else "No matches found."
    except Exception as e:
        return f"ERROR: An error occurred during grep. {str(e)}"

def write_to_scratchpad(content, mode='a'):
    try:
        write_mode = 'a' if mode == 'append' else 'w'
        with open(SCRATCHPAD_FILE, write_mode, encoding='utf-8', errors='replace') as f:
            f.write(content + "\n")
        return f"Successfully saved {len(content)} characters to scratchpad."
    except Exception as e:
        return f"ERROR: Could not write to scratchpad. {str(e)}"
