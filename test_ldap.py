from ldap3 import Server, Connection, ALL
import sys

print("Testing LDAP connection to localhost:10389")
try:
    user_dn = "uid=jsilva,ou=users,dc=empresa,dc=com"
    server = Server("ldap://127.0.0.1:10389", get_info=ALL)
    conn = Connection(server, user=user_dn, password="senha123")
    print("Binding...")
    success = conn.bind()
    print("Bind success:", success)
    if not success:
        print("Result:", conn.result)
except Exception as e:
    print("Exception!")
    import traceback
    traceback.print_exc()
