import json
from typing import Dict, Any, List
from agent.state import AgentState, TaskItem
from agent.llm import get_llm
from agent.utils import clean_json_string
from langchain_core.messages import SystemMessage, HumanMessage

def process_tasks_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Parses raw user input into structured tasks and professionalizes them.
    """
    raw_input = state.get("raw_tasks_input", "").strip()
    status_log = state.get("status_log", [])[:]
    status_log.append("Started task parsing and professional expansion...")
    
    if not raw_input:
        return {
            "error": "Task input is empty.",
            "status_log": status_log + ["Failed: Raw task input is empty."]
        }
        
    try:
        llm = get_llm(
            provider=state.get("llm_provider", ""),
            api_key=state.get("llm_api_key", "")
        )
        
        system_prompt = (
            "You are a professional business communication assistant. Your job is to take an intern's "
            "informal daily tasks list and parse it into structured tasks. "
            "For each task:\n"
            "1. Generate a concise, clear task title (2-5 words).\n"
            "2. Generate a professional explanation. Translate short/informal phrases into formal, "
            "action-oriented business English. Be specific, clear, and highlight the technical value.\n"
            "3. Identify a category (e.g., Backend, Frontend, Database, Testing, DevOps, documentation, etc.).\n"
            "4. Assign a status (default to 'Planned' or 'In Progress').\n\n"
            "You must return the output as a valid JSON list of objects with the keys: "
            "'title', 'description', 'category', 'status'. Do not output any markdown code blocks, "
            "preambles, or explanations other than the JSON itself."
        )
        
        user_prompt = f"Here is the intern's task list:\n{raw_input}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        content = response.content
        cleaned_content = clean_json_string(content)
        
        parsed_tasks = json.loads(cleaned_content, strict=False)
        
        if not isinstance(parsed_tasks, list):
            raise ValueError("LLM response did not parse as a JSON list.")
            
        # Validate task fields
        validated_tasks: List[TaskItem] = []
        for item in parsed_tasks:
            validated_tasks.append({
                "title": str(item.get("title", "Task Update")),
                "description": str(item.get("description", "")),
                "category": str(item.get("category", "General")),
                "status": str(item.get("status", "Planned"))
            })
            
        status_log.append(f"Successfully processed {len(validated_tasks)} tasks.")
        return {
            "tasks": validated_tasks,
            "status_log": status_log,
            "error": ""
        }
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        error_msg = f"Error in Task Processor: {str(e)}\n{tb}"
        status_log.append("Failed task parsing node.")
        return {
            "error": error_msg,
            "status_log": status_log
        }
