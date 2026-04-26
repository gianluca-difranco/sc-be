import json
import boto3
from fastapi import HTTPException
from core.config import config


def send_to_sqs(payload: dict, queue_url: str = None) -> None:
    """
    Serializza `payload` come JSON e lo invia alla coda SQS configurata.

    Args:
        payload: dizionario con i dati da inviare (deve essere JSON-serializzabile).
        queue_url: URL della coda SQS. Di default usa config.SQS_QUEUE_URL.

    Raises:
        HTTPException 502: se boto3 non riesce a contattare SQS.
    """
    try:
        sqs = boto3.client(
            "sqs", 
            region_name=config.AWS_REGION,
            endpoint_url=config.AWS_ENDPOINT_URL if config.AWS_ENDPOINT_URL else None
        )
        target_url = queue_url or config.SQS_QUEUE_URL
        if not target_url:
            print("Nessun SQS_QUEUE_URL fornito, salto invio SQS")
            return
        sqs.send_message(
            QueueUrl=target_url,
            MessageBody=json.dumps(payload),
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Errore nell'invio del messaggio alla coda SQS: {str(e)}",
        )
