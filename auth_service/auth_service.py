from ldap3 import Server, Connection
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LDAP_SERVER = "ldap"
LDAP_BASE_DN = "dc=empresa,dc=com"
LDAP_ADMIN_DN = "cn=admin,dc=empresa,dc=com"
LDAP_ADMIN_PASSWORD = "admin"


class LDAPConnection:
    def __init__(self):
        self.server = Server(LDAP_SERVER, get_info="ALL")
        self.connection = Connection(
            self.server,
            user=LDAP_ADMIN_DN,
            password=LDAP_ADMIN_PASSWORD
        )

    def bind(self) -> bool:
        return self.connection.bind()


def create_jwt(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, "secret_key", algorithm="HS256")


@app.get("/auth/siglas")
def get_siglas():
    try:
        ldap = LDAPConnection()
        ldap.bind()
        ldap.connection.search(
            search_base="ou=siglas,dc=empresa,dc=com",
            search_filter="(objectClass=groupOfNames)",
            attributes=["cn", "description", "member"]
        )

        siglas = [
            {
                "id": entry.entry_attributes_as_dict.get("cn", [""])[0],
                "nome": entry.entry_attributes_as_dict.get("description", [""])[0],
            }
            for entry in ldap.connection.entries
        ]

        return siglas
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/auth/siglas/{username}")
def get_users_siglas(username: str):
    try:
        ldap = LDAPConnection()
        ldap.bind()
        ldap.connection.search(
            search_base="ou=siglas,dc=empresa,dc=com",
            search_filter=f"(&(objectClass=groupOfNames)(member=uid={username},ou=users,dc=empresa,dc=com))",
            attributes=["cn", "description", "owner"]
        )

        siglas = [
            {

               "id": entry.entry_attributes_as_dict.get("cn", [""])[0] + " - " + entry.entry_attributes_as_dict.get("description", [""])[0],
               "owner": entry.entry_attributes_as_dict.get("owner", [""])[0].split(",")[0].split("=")[1]
            }
            for entry in ldap.connection.entries
        ]

        return siglas
    except Exception as e:
        return {"error": str(e)}


class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/auth/login")
def login(req: LoginRequest):
    """Autentica contra LDAP"""
    try:
        user_dn = f"uid={req.username},ou=users,dc=empresa,dc=com"
        user_conn = Connection(
            Server(LDAP_SERVER),
            user=user_dn,
            password=req.password
        )

        if user_conn.bind():
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


@app.get("/health")
def health():
    return {"status": "ok"}
