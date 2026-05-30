FROM osixia/openldap:1.5.0

# Copia apenas o bootstrap LDIF (que já contém OUs, usuários e siglas).
# O users.ldif NÃO é copiado pois seus dados já estão no 50-bootstrap.ldif
# e carregá-lo causaria erro 68 (LDAP_ALREADY_EXISTS).
COPY 50-bootstrap.ldif /container/service/slapd/assets/config/bootstrap/ldif/50-bootstrap.ldif
