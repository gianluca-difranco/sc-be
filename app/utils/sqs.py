import json
import boto3
from fastapi import HTTPException
from core.config import config


def send_to_sqs(payload: dict) -> None:
    """
    Serializza `payload` come JSON e lo invia alla coda SQS configurata.

    Args:
        payload: dizionario con i dati da inviare (deve essere JSON-serializzabile).

    Raises:
        HTTPException 502: se boto3 non riesce a contattare SQS.
    """
    try:
        sqs = boto3.client("sqs", region_name=config.AWS_REGION)
        sqs.send_message(
            QueueUrl=config.SQS_QUEUE_URL,
            MessageBody=json.dumps(payload),
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Errore nell'invio del messaggio alla coda SQS: {str(e)}",
        )
