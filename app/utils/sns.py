import boto3
import json
from fastapi import HTTPException
from core.config import config

def subscribe_user_to_tenant_topic(email: str, tenant_id: int) -> None:
    """
    Iscrive l'utente al topic SNS globale per le notifiche,
    impostando una filter policy per il tenant_id.
    """
    if not config.SNS_TOPIC_ARN:
        print("Nessun SNS_TOPIC_ARN configurato, salto la subscription SNS per:", email)
        return
        
    try:
        sns = boto3.client(
            "sns", 
            region_name=config.AWS_REGION,
            endpoint_url=config.AWS_ENDPOINT_URL if config.AWS_ENDPOINT_URL else None
        )
        
        # Policy: accetta solo messaggi che hanno l'attributo tenant_id uguale al tenant_id dell'utente
        filter_policy = {
            "tenant_id": [str(tenant_id)]
        }
        
        sns.subscribe(
            TopicArn=config.SNS_TOPIC_ARN,
            Protocol="email",
            Endpoint=email,
            ReturnSubscriptionArn=True,
            Attributes={
                "FilterPolicy": json.dumps(filter_policy)
            }
        )
    except Exception as e:
        print(f"Errore nella subscription SNS per {email}: {e}")
        # Non blocchiamo la creazione dell'utente se SNS fallisce
