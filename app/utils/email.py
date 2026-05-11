import smtplib
from email.message import EmailMessage
from core.config import config
import logging

logger = logging.getLogger(__name__)

def send_set_password_email(email_to: str, token: str):
    """
    Invia una mail all'utente con il link per impostare la password.
    """
    subject = "Benvenuto su FantaCloud - Imposta la tua password"
    link = f"{config.FRONTEND_URL}/set-password?token={token}"
    body = f"""
    Ciao!
    
    Sei stato invitato a registrarti su FantaCloud.
    Per completare la configurazione del tuo account e impostare una password, clicca sul link seguente:
    
    {link}
    
    Se non hai richiesto questa registrazione, puoi ignorare l'email.
    
    A presto,
    Il team di FantaCloud
    """
    
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = config.SMTP_USER or "noreply@fantacloud.local"
    msg['To'] = email_to

    try:
        if config.USE_SES:
            import boto3
            from botocore.exceptions import ClientError
            
            sender = config.SES_SENDER_EMAIL
            ses_client = boto3.client('ses', region_name=config.AWS_SES_REGION)
            try:
                response = ses_client.send_email(
                    Destination={
                        'ToAddresses': [email_to],
                    },
                    Message={
                        'Body': {
                            'Text': {
                                'Charset': "UTF-8",
                                'Data': body,
                            },
                        },
                        'Subject': {
                            'Charset': "UTF-8",
                            'Data': subject,
                        },
                    },
                    Source=sender,
                )
                logger.info(f"Email inviata con successo tramite SES a {email_to}, MessageId: {response['MessageId']}")
            except ClientError as e:
                logger.error(f"Errore SES durante l'invio dell'email a {email_to}: {e.response['Error']['Message']}")
            return

        # Fallback a SMTP
        if not config.SMTP_HOST:
            logger.warning("SMTP_HOST non configurato, la mail non verrà inviata.")
            return

        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            if config.SMTP_USER and config.SMTP_PASSWORD:
                server.starttls()
                server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(msg)
            logger.info(f"Email inviata con successo tramite SMTP a {email_to}")
    except Exception as e:
        logger.error(f"Errore durante l'invio dell'email a {email_to}: {e}")
