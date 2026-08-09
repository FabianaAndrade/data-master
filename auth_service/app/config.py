"""
Configurações do auth_service.
"""

# LDAP
LDAP_SERVER = "ldap"
LDAP_BASE_DN = "dc=empresa,dc=com"
LDAP_ADMIN_DN = "cn=admin,dc=empresa,dc=com"
LDAP_ADMIN_PASSWORD = "admin"

# JWT
JWT_SECRET = "secret_key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 1