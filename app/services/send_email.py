from smtplib import SMTP_SSL
from email.message import EmailMessage
from ssl import create_default_context
from app.core.config import settings


def send_reset_password_email(email_to: str, token: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = "Redefinição de Senha",
    msg["From"] = settings["WEBMAIL_USUARIO"]
    msg["To"] = email_to

    reset_link = f"https://carvalima-helpdesk.carvalima-teste.duckdns.org:8086/reset-password?token={token}"

    msg.set_content(f"""
        <h3>Recuperação de Senha - Finan Smart</h3>
        <p>Você solicitou a redefinição de sua senha.</p>
        <p>Clique no link abaixo para criar uma nova senha:</p>
        <a href="{reset_link}" style="padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">
            Redefinir Minha Senha
        </a>
        <p>Este link expira em 30 minutos.</p>
        <p>Se não foi você, ignore este e-mail.</p>
    """)


    with SMTP_SSL("smtp.gmail.com", 465, context=create_default_context()) as server:
        server.login(settings["WEBMAIL_USUARIO"], settings["WEBMAIL_SENHA"])
        server.send_message(msg)
