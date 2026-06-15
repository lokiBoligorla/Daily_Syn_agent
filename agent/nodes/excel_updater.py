import json
from datetime import datetime
from typing import Dict, Any, List
from agent.state import AgentState
from agent.llm import get_llm
from tools.excel_tool import find_excel_file, get_excel_headers, append_task_rows_to_excel
from agent.utils import clean_json_string
from langchain_core.messages import SystemMessage, HumanMessage

def excel_updater_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Locates Excel file, reads headers, maps tasks to headers via LLM, and appends them.
    """
    status_log = state.get("status_log", [])[:]
    status_log.append("Started Excel update node...")
    
    if state.get("error"):
        status_log.append("Skipping Excel update due to upstream error.")
        return {"status_log": status_log}
        
    tasks = state.get("tasks", [])
    if not tasks:
        status_log.append("No tasks found to write to Excel.")
        return {"error": "No tasks to write.", "status_log": status_log}
        
    try:
        # Prioritize the excel_path passed in state (e.g. from user file upload)
        excel_path = state.get("excel_path") or find_excel_file()
        if not excel_path:
            raise FileNotFoundError("Could not find any Excel file in state, data/ folder, or root directory.")
            
        status_log.append(f"Located Excel tracker at: {excel_path}")
        
        # 2. Get Headers
        headers = get_excel_headers(excel_path)
        status_log.append(f"Excel columns detected: {headers}")
        
        # 3. Use LLM to map tasks to Excel headers
        llm = get_llm(
            provider=state.get("llm_provider", ""),
            api_key=state.get("llm_api_key", "")
        )
        today_str = datetime.now().strftime("%d/%m/%Y")
        
        system_prompt = (
            "You are a data mapper assistant. Your job is to map structured daily tasks "
            "to the exact column headers of an Excel sheet. You must match the keys of your output objects "
            "exactly to the strings in the Excel headers list.\n\n"
            "Here are the mapping rules:\n"
            "- The keys of each JSON object MUST be the exact strings from the Excel headers list.\n"
            "- For any key that represents an ID or serial number (e.g. 'S.No', 'ID', 'Serial', 'No.'), set its value to 'INCREMENT'.\n"
            f"- For any key that represents a Date (e.g. 'Date', 'Day'), set its value to '{today_str}'.\n"
            "- For any key that represents an Intern/Employee Name (e.g. 'Name', 'Intern Name'), set its value to 'Lokesh'.\n"
            "- For keys representing task titles/details/categories/status (e.g. 'Task', 'Description', 'status'), map them to the corresponding task properties.\n"
            "- For all other keys representing empty columns (e.g. starting with '[Empty Header - Col ...]'), set their value to \"\".\n\n"
            "Example:\n"
            "If Excel headers are: [\"[Empty Header - Col A]\", \"Date\", \"Task\", \"status\"]\n"
            "Your output object must look exactly like this:\n"
            "{\n"
            "  \"[Empty Header - Col A]\": \"\",\n"
            f"  \"Date\": \"{today_str}\",\n"
            "  \"Task\": \"Implement secure OAuth2 module...\",\n"
            "  \"status\": \"Planned\"\n"
            "}\n\n"
            "You MUST output a valid JSON list of objects. Each key in each object must match a header from the list. "
            "Do not output any markdown code fences, preambles, or explanations other than the raw JSON."
        )
        
        user_prompt = (
            f"Excel headers list:\n{json.dumps(headers)}\n\n"
            f"Tasks to write:\n{json.dumps(tasks)}\n\n"
            "Please generate the mapped JSON array."
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        content = response.content
        cleaned_content = clean_json_string(content)
        
        mapped_rows = json.loads(cleaned_content, strict=False)
        
        if not isinstance(mapped_rows, list):
            raise ValueError("Mapped rows response did not parse as a JSON list.")
            
        # 4. Write to Excel
        append_task_rows_to_excel(excel_path, mapped_rows)
        
        status_log.append("Successfully appended task rows to Excel workbook and saved.")
        return {
            "excel_path": excel_path,
            "excel_headers": headers,
            "excel_updated": True,
            "status_log": status_log,
            "error": ""
        }
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        error_msg = f"Error in Excel Updater: {str(e)}\n{tb}"
        status_log.append("Failed Excel updater node.")
        return {
            "error": error_msg,
            "status_log": status_log
        }
