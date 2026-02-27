from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from schemas.email import EmailSchema



async def send_email_smtp(email_data: EmailSchema):  
        sender_email = "edquestsocial@gmail.com"
        sender_password = "rklwbmncxmsiqtxi"
        smtp_server = "smtp.gmail.com"
        smtp_port = 587 # or 465 for SSL

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email_data.recipient_email
        msg['Subject'] = email_data.subject
        msg.attach(MIMEText(email_data.body, 'plain')) # or 'html'

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls() # or server.ehlo() and server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, email_data.recipient_email, msg.as_string())
            return {"message": "Email sent successfully via SMTP"}
        except Exception as e:
            return {"error": f"Failed to send email: {e}"}