import json
from datetime import datetime
from typing import Dict, Any
from agent.state import AgentState
from agent.llm import get_llm
from agent.utils import clean_json_string
from langchain_core.messages import SystemMessage, HumanMessage

def email_generator_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Formulates the professional daily update email using LLM.
    """
    status_log = state.get("status_log", [])[:]
    status_log.append("Started email generation node...")
    
    if state.get("error"):
        status_log.append("Skipping email generation due to upstream error.")
        return {"status_log": status_log}
        
    tasks = state.get("tasks", [])
    if not tasks:
        status_log.append("No tasks found to generate email.")
        return {"error": "No tasks to email.", "status_log": status_log}
        
    try:
        llm = get_llm(
            provider=state.get("llm_provider", ""),
            api_key=state.get("llm_api_key", "")
        )
        today_str = datetime.now().strftime("%d/%m/%Y")
        
        system_prompt = (
            "You are a professional business writer. Your job is to draft a daily update email "
            "summarizing an intern's planned tasks for the day.\n\n"
            "Here are the writing requirements:\n"
            "- Professional, polite, and enthusiastic tone.\n"
            "- Clear structure with a numbered or bulleted task-wise breakdown.\n"
            "- For each task, include a brief professional explanation of the work and its goals.\n"
            "- Sign the email with the name: Lokesh.\n\n"
            "You MUST format your output exactly as shown below, using the literal tags ===SUBJECT=== and ===BODY=== as delimiters:\n\n"
            "===SUBJECT===\n"
            f"Daily Task Update - {today_str}\n"
            "===BODY===\n"
            "Dear Team,\n\n"
            "I would like to share my planned tasks for today.\n\n"
            "1. Task Title\n"
            "   - Detailed professional explanation.\n\n"
            "Regards,\n"
            "Lokesh\n\n"
            "Do not output any markdown code blocks, JSON, or explanations other than the tags and content."
        )
        
        user_prompt = f"Tasks for today:\n{json.dumps(tasks)}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Strip markdown fences if LLM accidentally outputted them
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()
            
        if "===SUBJECT===" not in content or "===BODY===" not in content:
            raise ValueError("LLM response did not contain required ===SUBJECT=== and ===BODY=== tags.")
            
        parts = content.split("===BODY===")
        subject_part = parts[0].replace("===SUBJECT===", "").strip()
        body = parts[1].strip()
        
        # Clean quotes
        subject = subject_part.strip('"' + "'" + " \n\t")
        
        if not body:
            raise ValueError("Email body generated was empty.")
            
        status_log.append("Successfully generated daily task update email draft.")
        return {
            "email_subject": subject,
            "email_body": body,
            "status_log": status_log,
            "error": ""
        }
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        error_msg = f"Error in Email Generator: {str(e)}\n{tb}"
        status_log.append("Failed email generator node.")
        return {
            "error": error_msg,
            "status_log": status_log
        }
