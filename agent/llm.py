import os
from datetime import datetime
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field

load_dotenv()

class MockLLM(BaseChatModel):
    """
    A Mock LangChain Chat Model for testing the reporting agent system offline
    without requiring active LLM API keys.
    """
    model_name: str = "mock"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt_text = messages[-1].content
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # 1. Check if it's Task Parsing & Expansion
        if "structured tasks" in prompt_text.lower() or "intern's task list" in prompt_text.lower():
            response_content = """[
              {
                "title": "Build Authentication Module",
                "description": "Implement and test secure user authentication and authorization functionality to ensure proper access control and user management.",
                "category": "Backend",
                "status": "Planned"
              },
              {
                "title": "Fix API Integration Issues",
                "description": "Resolve connectivity and data sync anomalies within external API integrations to restore stable endpoint communication.",
                "category": "Backend",
                "status": "In Progress"
              },
              {
                "title": "Test RAG Pipeline",
                "description": "Evaluate retrieval-augmented generation output quality and latency parameters to optimize knowledge retrieval accuracy.",
                "category": "Testing",
                "status": "Planned"
              },
              {
                "title": "Review Deployment Workflow",
                "description": "Audit deployment pipelines, environment variables, and release configurations to streamline production deployment.",
                "category": "DevOps",
                "status": "Planned"
              }
            ]"""
            
        # 2. Check if it's Excel dynamic header mapping
        elif "excel headers list" in prompt_text.lower() or "excel headers" in prompt_text.lower():
            import json
            import re
            
            # Find and parse headers list
            headers = []
            for msg in messages:
                if "excel headers list" in msg.content.lower():
                    # Attempt to extract JSON list
                    match = re.search(r"(\[.*?\])", msg.content, re.DOTALL)
                    if match:
                        try:
                            headers = json.loads(match.group(1))
                        except Exception:
                            pass
            
            if not headers:
                headers = ["Date", "Task Title", "Professional Explanation", "Status", "Intern Name"]
                
            # Formulate mapped data rows
            mapped_rows = []
            mock_tasks = [
                ("Build Authentication Module", "Implement and test secure user authentication and authorization functionality to ensure proper access control and user management.", "Backend", "Planned"),
                ("Fix API Integration Issues", "Resolve connectivity and data sync anomalies within external API integrations to restore stable endpoint communication.", "Backend", "In Progress"),
                ("Test RAG Pipeline", "Evaluate retrieval-augmented generation output quality and latency parameters to optimize knowledge retrieval accuracy.", "Testing", "Planned"),
                ("Review Deployment Workflow", "Audit deployment pipelines, environment variables, and release configurations to streamline production deployment.", "DevOps", "Planned")
            ]
            
            for title, desc, cat, status in mock_tasks:
                row_map = {}
                for h in headers:
                    h_lower = h.lower()
                    if any(kw in h_lower for kw in ["s.no", "sno", "id", "serial", "no.", "seq", "#"]):
                        row_map[h] = "INCREMENT"
                    elif "date" in h_lower:
                        row_map[h] = today_str
                    elif any(kw in h_lower for kw in ["name", "intern", "employee"]):
                        row_map[h] = "Lokesh"
                    elif any(kw in h_lower for kw in ["title", "task", "name"]):
                        row_map[h] = title
                    elif any(kw in h_lower for kw in ["desc", "detail", "explanation"]):
                        row_map[h] = desc
                    elif "status" in h_lower:
                        row_map[h] = status
                    elif "cat" in h_lower or "module" in h_lower:
                        row_map[h] = cat
                    else:
                        row_map[h] = ""
                mapped_rows.append(row_map)
                
            response_content = json.dumps(mapped_rows)
            
        # 3. Default to Email Generation
        else:
            response_content = f"""{{
              "subject": "Daily Task Update - {today_str}",
              "body": "Dear Team,\\n\\nI would like to share my planned tasks for today.\\n\\n1. Build Authentication Module\\n   - Implement and test secure user authentication and authorization functionality to ensure proper access control and user management.\\n\\n2. Fix API Integration Issues\\n   - Resolve connectivity and data sync anomalies within external API integrations to restore stable endpoint communication.\\n\\n3. Test RAG Pipeline\\n   - Evaluate retrieval-augmented generation output quality and latency parameters to optimize knowledge retrieval accuracy.\\n\\n4. Review Deployment Workflow\\n   - Audit deployment pipelines, environment variables, and release configurations to streamline production deployment.\\n\\nPlease find the updated tracker attached for reference.\\n\\nRegards,\\nLokesh"
            }}"""
            
        message = AIMessage(content=response_content)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "mock"

def get_llm(provider: str = "", api_key: str = "") -> BaseChatModel:
    """
    Dynamically loads and returns the selected LLM based on parameters or environment variables.
    """
    provider = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()
    
    if provider == "mock":
        return MockLLM()
        
    elif provider == "gemini":
        active_key = api_key or os.getenv("GEMINI_API_KEY")
        if not active_key:
            # Automatic fallback to mock with console notice if no key is supplied
            print("[Warning] GEMINI_API_KEY not found. Falling back to Mock LLM.")
            return MockLLM()
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=active_key, temperature=0.2)
        
    elif provider == "openai":
        active_key = api_key or os.getenv("OPENAI_API_KEY")
        if not active_key:
            print("[Warning] OPENAI_API_KEY not found. Falling back to Mock LLM.")
            return MockLLM()
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", api_key=active_key, temperature=0.2)
        
    elif provider == "nvidia":
        active_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not active_key:
            print("[Warning] NVIDIA_API_KEY not found. Falling back to Mock LLM.")
            return MockLLM()
        # Default to the active meta/llama-3.1-8b-instruct model, allow override via env
        model_name = os.getenv("NVIDIA_MODEL_NAME", "meta/llama-3.1-8b-instruct").strip()
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name, 
            api_key=active_key, 
            base_url="https://integrate.api.nvidia.com/v1",
            temperature=0.2
        )
    else:
        # Fallback to mock
        print(f"[Warning] Unknown provider '{provider}'. Falling back to Mock LLM.")
        return MockLLM()
