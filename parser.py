# parser.py - AI Output Interpreter (Draft-Safe Edition)
import os, sys, re

def smart_parse_ai_output(raw_text, turn_marker=None):
    if not raw_text: return None
    
    ai_text = raw_text
    if turn_marker:
        marker_idx = raw_text.rfind(turn_marker)
        if marker_idx != -1:
            ai_text = raw_text[marker_idx + len(turn_marker):]
        else:
            match = re.search(r'\[SYS_MARKER_\d+\]', raw_text)
            if match: ai_text = raw_text[match.end():]

    if any(p in ai_text.lower() for p in["rate limit exceeded", "quota exceeded", "resource has been exhausted", "internal server error"]): 
        return "RATE_LIMIT"

    ai_text = re.sub(r'```(?:xml|html)?\s*', '', ai_text, flags=re.IGNORECASE)
    ai_text = re.sub(r'```\s*', '', ai_text)

    # THE DRAFT FIX: Only grab the very first <response> block!
    # This completely ignores Draft 2, Draft 3, and any UI garbage below the main response.
    response_match = re.search(r'<response>(.*?)</response>', ai_text, re.DOTALL | re.IGNORECASE)
    if response_match:
        ai_text = response_match.group(1)

    tools_to_run =[]
    
    tool_blocks = re.finditer(r'<execute_tool>(.*?)</execute_tool>', ai_text, re.DOTALL | re.IGNORECASE)
    
    for block_match in tool_blocks:
        block = block_match.group(1)
        tool_data = {}
        
        name_match = re.search(r'<tool_name>(.*?)</tool_name>', block, re.DOTALL | re.IGNORECASE)
        if name_match:
            tool_data['tool'] = name_match.group(1).strip()
        else:
            continue 
            
        parameters = {}
        param_matches = re.finditer(r'<([a-zA-Z0-9_]+)>(.*?)</\1>', block, re.DOTALL | re.IGNORECASE)
        
        for p_match in param_matches:
            tag = p_match.group(1).lower()
            if tag != 'tool_name':
                val = p_match.group(2).strip()
                val = re.sub(r'^<!\[CDATA\[(.*)\]\]>$', r'\1', val, flags=re.DOTALL | re.IGNORECASE)
                
                if val.startswith('\n'): val = val[1:]
                if val.endswith('\n'): val = val[:-1]
                
                parameters[tag] = val
                
        tool_data['parameters'] = parameters
        tools_to_run.append(tool_data)
        
    if tools_to_run:
        return[{"status": "continue", "message": "", "tools": tools_to_run}]
        
    return "PARSE_ERROR"
