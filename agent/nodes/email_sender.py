import os
from dotenv import load_dotenv
from typing import Dict, Any
from agent.state import AgentState
from tools.email_tool import send_email_with_attachment

load_dotenv()

def email_sender_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node: Sends the compiled email with the Excel sheet attached using SMTP.
    """
    status_log = state.get("status_log", [])[:]
    status_log.append("Started email sending node...")
    
    if state.get("error"):
        status_log.append("Skipping email sending due to upstream error.")
        return {"status_log": status_log}
        
    subject = state.get("email_subject")
    body = state.get("email_body")
    excel_path = state.get("excel_path")
    excel_updated = state.get("excel_updated", False)
    
    if not subject or not body:
        status_log.append("Subject or Body is missing. Cannot send email.")
        return {"error": "Email details missing.", "status_log": status_log}
        
    if not excel_updated or not excel_path:
        status_log.append("Excel attachment is missing or was not updated. Cannot send email.")
        return {"error": "Excel attachment missing or unupdated.", "status_log": status_log}
        
    try:
        # Load SMTP settings and recipients from state (or fallback to environment)
        smtp_server = (state.get("smtp_server") or os.getenv("SMTP_SERVER", "")).strip()
        smtp_port_str = str(state.get("smtp_port") or os.getenv("SMTP_PORT", "")).strip()
        sender_email = (state.get("sender_email") or os.getenv("SENDER_EMAIL", "")).strip()
        sender_password = (state.get("sender_password") or os.getenv("SENDER_PASSWORD", "")).strip()
        
        # Load recipients
        to_email = (state.get("to_email") or os.getenv("TEAM_LEAD_1", "")).strip()
        cc_email = (state.get("cc_email") or os.getenv("TEAM_LEAD_2", "")).strip()
        
        if not to_email and not cc_email:
            raise ValueError("No recipient email addresses found. Please configure the recipients (To/Cc) fields.")
            
        # Route To/Cc
        route_to = to_email if to_email else cc_email
        route_cc = cc_email if to_email and cc_email else None
            
        # Basic validations
        if not smtp_server or not smtp_port_str or not sender_email or not sender_password:
            missing = [k for k, v in [
                ("SMTP_SERVER", smtp_server),
                ("SMTP_PORT", smtp_port_str),
                ("SENDER_EMAIL", sender_email),
                ("SENDER_PASSWORD", sender_password)
            ] if not v]
            raise ValueError(f"SMTP Configuration is incomplete. Missing parameters: {', '.join(missing)}")
            
        try:
            smtp_port = int(smtp_port_str)
        except ValueError:
            raise ValueError(f"SMTP_PORT must be an integer, got: '{smtp_port_str}'")
            
        status_log.append(f"Sending email to: {route_to} (Cc: {route_cc}) via {smtp_server}:{smtp_port}...")
        
        # Call tool
        send_email_with_attachment(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            sender_email=sender_email,
            sender_password=sender_password,
            to_email=route_to,
            cc_email=route_cc,
            subject=subject,
            body=body,
            attachment_path=excel_path
        )
        
        status_log.append("Email successfully sent to team leads.")
        return {
            "email_sent": True,
            "status_log": status_log,
            "error": ""
        }
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        error_msg = f"Error in Email Sender: {str(e)}\n{tb}"
        status_log.append("Failed email sending node.")
        return {
            "error": error_msg,
            "status_log": status_log
        }
