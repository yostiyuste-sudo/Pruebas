import base64
import json
import urllib.request
import urllib.error
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

class BrevoEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        api_key = getattr(settings, 'BREVO_API_KEY', '')
        if not api_key:
            print("[BREVO BACKEND] No BREVO_API_KEY configurada. Imprimiendo en consola.")
            for message in email_messages:
                print(f"--- SIMULACIÓN DE CORREO ---")
                print(f"Para: {message.to}")
                print(f"Asunto: {message.subject}")
                print(f"Cuerpo: {message.body}")
            return len(email_messages)

        sent_count = 0
        for message in email_messages:
            try:
                # Obtener remitente
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', '') or message.from_email or 'onboarding@resend.dev'
                sender_name = "Constructora Dyco"
                if '<' in from_email and '>' in from_email:
                    parts = from_email.split('<')
                    sender_name = parts[0].strip()
                    from_email = parts[1].replace('>', '').strip()

                # Destinatarios
                to_list = []
                for t in message.to:
                    to_list.append({"email": t})

                # Contenido HTML y texto plano
                html_content = ""
                text_content = message.body or ""
                
                # Extraer cuerpo HTML de EmailMultiAlternatives
                if hasattr(message, 'alternatives'):
                    for alt_body, alt_type in message.alternatives:
                        if alt_type == 'text/html':
                            html_content = alt_body

                if not html_content:
                    html_body = text_content.replace('\n', '<br>')
                    html_content = f"<html><body>{html_body}</body></html>"

                # Procesar adjuntos
                attachments = []
                for attachment in message.attachments:
                    # attachment puede ser una tupla (filename, content, mimetype) o un objeto MIMEBase
                    filename = ""
                    content = b""
                    if isinstance(attachment, tuple):
                        filename = attachment[0]
                        content = attachment[1]
                    else:
                        filename = attachment.get_filename() or "adjunto"
                        content = attachment.get_payload(decode=True)
                    
                    if content:
                        b64_content = base64.b64encode(content).decode('utf-8')
                        attachments.append({
                            "content": b64_content,
                            "name": filename
                        })

                payload = {
                    "sender": {"name": sender_name, "email": from_email},
                    "to": to_list,
                    "subject": message.subject,
                    "htmlContent": html_content
                }
                if text_content:
                    payload["textContent"] = text_content
                if attachments:
                    payload["attachment"] = attachments

                req = urllib.request.Request(
                    "https://api.brevo.com/v3/smtp/email",
                    data=json.dumps(payload).encode('utf-8'),
                    headers={
                        "api-key": api_key,
                        "Content-Type": "application/json"
                    },
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=12) as response:
                    res_body = response.read().decode('utf-8')
                    print(f"[BREVO BACKEND] Correo enviado exitosamente a {message.to}: {res_body}")
                    sent_count += 1
            except urllib.error.HTTPError as e:
                res_body = e.read().decode('utf-8') if e.fp else str(e)
                print(f"[BREVO BACKEND ERROR] Error HTTP: {res_body}")
            except Exception as e:
                print(f"[BREVO BACKEND ERROR] Excepción al enviar: {e}")

        return sent_count
