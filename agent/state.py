from typing import List, Dict, Any, TypedDict

class TaskItem(TypedDict):
    title: str
    description: str
    category: str
    status: str

class AgentState(TypedDict):
    raw_tasks_input: str
    preview_mode: bool  # If True, the graph stops at email generation
    tasks: List[TaskItem]
    excel_path: str
    excel_headers: List[str]
    excel_updated: bool
    email_subject: str
    email_body: str
    email_sent: bool
    status_log: List[str]
    error: str
    
    # Thread-safe Configuration parameters (injected from user UI session)
    llm_provider: str
    llm_api_key: str
    smtp_server: str
    smtp_port: str
    sender_email: str
    sender_password: str
    to_email: str
    cc_email: str

