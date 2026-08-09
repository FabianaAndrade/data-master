"""
Cliente LDAP e utilitários de autenticação.
"""
from datetime import datetime, timedelta, timezone

import jwt
from ldap3 import Server, Connection

from .config import (
    LDAP_SERVER,
    LDAP_BASE_DN,
    LDAP_ADMIN_DN,
    LDAP_ADMIN_PASSWORD,
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRATION_HOURS,
)


class LDAPClient:
    """Cliente para operações no servidor LDAP."""

    def __init__(self):
        self.server = Server(LDAP_SERVER, get_info="ALL")
        self.connection = Connection(
            self.server,
            user=LDAP_ADMIN_DN,
            password=LDAP_ADMIN_PASSWORD,
        )
        self.connection.bind()

    def authenticate(self, username: str, password: str) -> bool:
        """Tenta bind no LDAP com as credenciais do usuário."""
        user_dn = f"uid={username},ou=users,{LDAP_BASE_DN}"
        user_conn = Connection(Server(LDAP_SERVER), user=user_dn, password=password)
        return user_conn.bind()

    def get_siglas(self) -> list:
        """Busca todas as siglas cadastradas no LDAP."""
        self.connection.search(
            search_base=f"ou=siglas,{LDAP_BASE_DN}",
            search_filter="(objectClass=groupOfNames)",
            attributes=["cn", "description", "member"],
        )
        return [
            {
                "id": entry.entry_attributes_as_dict.get("cn", [""])[0],
                "nome": entry.entry_attributes_as_dict.get("description", [""])[0],
            }
            for entry in self.connection.entries
        ]

    def get_user_siglas(self, username: str) -> list:
        """Busca as siglas das quais o usuário é membro no LDAP."""
        self.connection.search(
            search_base=f"ou=siglas,{LDAP_BASE_DN}",
            search_filter=f"(&(objectClass=groupOfNames)(member=uid={username},ou=users,{LDAP_BASE_DN}))",
            attributes=["cn", "description", "owner"],
        )
        return [
            {
                "id": entry.entry_attributes_as_dict.get("cn", [""])[0]
                    + " - "
                    + entry.entry_attributes_as_dict.get("description", [""])[0],
                "owner": entry.entry_attributes_as_dict.get("owner", [""])[0]
                    .split(",")[0]
                    .split("=")[1],
            }
            for entry in self.connection.entries
        ]


def create_jwt(username: str) -> str:
    """Gera um token JWT para o usuário autenticado."""
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
