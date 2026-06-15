import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional

def send_email_with_attachment(
    smtp_server: str,
    smtp_port: int,
    sender_email: str,
    sender_password: str,
    to_email: str,
    cc_email: Optional[str],
    subject: str,
    body: str,
    attachment_path: str
) -> None:
    """
    Sends an email with a file attachment via SMTP supporting To and Cc fields.
    """
    # 1. Build the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    
    # Parse multiple comma-separated emails for SMTP routing
    to_list = [email.strip() for email in to_email.split(",") if email.strip()]
    all_recipients = to_list.copy()
    
    if cc_email and cc_email.strip():
        msg['Cc'] = cc_email
        cc_list = [email.strip() for email in cc_email.split(",") if email.strip()]
        all_recipients.extend(cc_list)
        
    msg['Subject'] = subject
    
    # Attach body text
    msg.attach(MIMEText(body, 'plain'))
    
    # 2. Attach the Excel tracker
    if not os.path.exists(attachment_path):
        raise FileNotFoundError(f"Attachment file not found at: {attachment_path}")
        
    filename = os.path.basename(attachment_path)
    with open(attachment_path, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )
    msg.attach(part)
    
    # 3. Establish SMTP connection and send
    # Determine SSL/TLS
    is_ssl = int(smtp_port) == 465
    
    if is_ssl:
        server = smtplib.SMTP_SSL(smtp_server, int(smtp_port), timeout=15)
    else:
        server = smtplib.SMTP(smtp_server, int(smtp_port), timeout=15)
        server.starttls()
        
    try:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, all_recipients, msg.as_string())
    finally:
        server.quit()
