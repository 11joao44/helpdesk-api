from smtplib import SMTP_SSL
from email.message import EmailMessage
from ssl import create_default_context
from app.core.config import settings


def send_reset_password_email(email_to: str, token: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = "Redefinição de Senha"
    msg["From"] = settings["WEBMAIL_USUARIO"]
    msg["To"] = email_to

    reset_link = f"https://carvalima-helpdesk.carvalima-teste.duckdns.org:8086/reset-password?token={token}"

    msg.set_content(f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Recuperação de Senha - Finan Smart</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f8ff;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f0f8ff; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 520px; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 24px rgba(10, 10, 83, 0.12); overflow: hidden;">
                        
                        <!-- Header com gradiente azul escuro para ciano -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #0a0a53 0%, #0066aa 50%, #00ccff 100%); padding: 40px 40px 30px; text-align: center;">
                                <div style="width: 64px; height: 64px; background-color: rgba(255,255,255,0.15); border-radius: 16px; margin: 0 auto 16px; display: inline-block; line-height: 64px; border: 2px solid rgba(0, 204, 255, 0.4);">
                                    <span style="font-size: 32px;">🔐</span>
                                </div>
                                <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">Finan Smart</h1>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <!-- Título com cor primária azul escuro -->
                                <h2 style="margin: 0 0 16px; color: #0a0a53; font-size: 22px; font-weight: 600; text-align: center;">
                                    Recuperação de Senha
                                </h2>
                                
                                <!-- Texto com preto suave -->
                                <p style="margin: 0 0 24px; color: #333333; font-size: 15px; line-height: 1.6; text-align: center;">
                                    Recebemos uma solicitação para redefinir a senha da sua conta. Clique no botão abaixo para criar uma nova senha.
                                </p>
                                
                                <!-- Botão com gradiente da marca -->
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td align="center" style="padding: 8px 0 32px;">
                                            <a href="{reset_link}" target="_blank" style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #0a0a53 0%, #00ccff 100%); color: #ffffff; text-decoration: none; border-radius: 12px; font-size: 15px; font-weight: 600; box-shadow: 0 4px 14px rgba(10, 10, 83, 0.35);">
                                                Redefinir Minha Senha
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Warning box com tom ciano -->
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #e6faff; border-radius: 12px; border-left: 4px solid #00ccff;">
                                    <tr>
                                        <td style="padding: 16px 20px;">
                                            <p style="margin: 0; color: #0a0a53; font-size: 13px; line-height: 1.5;">
                                                <strong>⏱️ Este link expira em 30 minutos.</strong><br>
                                                Se você não solicitou esta alteração, ignore este e-mail.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Divider com cor accent -->
                        <tr>
                            <td style="padding: 0 40px;">
                                <hr style="border: none; border-top: 2px solid #00ccff; margin: 0; opacity: 0.3;">
                            </td>
                        </tr>
                        
                        <!-- Footer com cores da marca -->
                        <tr>
                            <td style="padding: 24px 40px 32px; text-align: center;">
                                <p style="margin: 0 0 8px; color: #0a0a53; font-size: 13px; opacity: 0.7;">
                                    © 2025 Finan Smart. Todos os direitos reservados.
                                </p>
                                <p style="margin: 0; color: #666666; font-size: 12px;">
                                    Este é um e-mail automático, por favor não responda.
                                </p>
                            </td>
                        </tr>
                        
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """, subtype='html')

    with SMTP_SSL("smtp.gmail.com", 465, context=create_default_context()) as server:
        server.login(settings["WEBMAIL_USUARIO"], settings["WEBMAIL_SENHA"])
        server.send_message(msg)

