"""
Configurações do auth_service.
"""
import os

LDAP_SERVER = os.getenv("LDAP_SERVER", "ldap")
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "dc=empresa,dc=com")
LDAP_ADMIN_DN = os.getenv("LDAP_ADMIN_DN", "cn=admin,dc=empresa,dc=com")
LDAP_ADMIN_PASSWORD = os.getenv("LDAP_ADMIN_PASSWORD", "")

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 1