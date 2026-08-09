"""
Endpoints do auth_service.
"""
from fastapi import APIRouter, HTTPException

from .ldap_client import LDAPClient, create_jwt
from .schemas import LoginRequest

router = APIRouter()


@router.get("/auth/siglas")
def get_siglas():
    """Retorna todas as siglas cadastradas no LDAP."""
    try:
        client = LDAPClient()
        return client.get_siglas()
    except Exception as e:
        return {"error": str(e)}


@router.get("/auth/siglas/{username}")
def get_users_siglas(username: str):
    """Retorna as siglas das quais o usuário é membro."""
    try:
        client = LDAPClient()
        return client.get_user_siglas(username)
    except Exception as e:
        return {"error": str(e)}


@router.post("/auth/login")
def login(req: LoginRequest):
    """Autentica o usuário contra o LDAP e retorna um JWT."""
    try:
        client = LDAPClient()
        if client.authenticate(req.username, req.password):
            token = create_jwt(req.username)
            return {"token": token, "user": req.username}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print("LOGIN ERROR TRACEBACK:", err_msg, flush=True)
        raise HTTPException(status_code=500, detail=str(err_msg))
