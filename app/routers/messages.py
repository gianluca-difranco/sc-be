from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.auth import require_role
from app.utils.sqs import send_to_sqs

router = APIRouter(prefix="/messages", tags=["messages"])


class MessageCreate(BaseModel):
    content: str


@router.post("/send", status_code=200)
def send_message(
    body: MessageCreate,
    current_user=Depends(require_role(["TA"])),
):
    """
    Invia un messaggio alla coda SQS.
    Solo i Tenant Admin (TA) possono usare questo endpoint.
    Il messaggio viene arricchito con il tenant_id dell'utente autenticato.
    """
    content = body.content.strip()
    if not content:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Il messaggio non può essere vuoto.")

    payload = {
        "tenant_id": current_user.tenant_id,
        "content": content,
    }

    send_to_sqs(payload)

    return {"detail": "Messaggio inviato con successo."}
