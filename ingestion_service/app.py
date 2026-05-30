from ldap3 import Server, Connection

server = Server("ldap://localhost:10389")
conn = Connection(server, user="cn=admin,dc=empresa,dc=com", password="admin123")
if conn.bind():
    print("Bind successful")
else:
    print("Bind failed:", conn.result)

print("Connection:", conn)

# Query
username = "jsilva"
conn.search(
    search_base="ou=siglas,dc=empresa,dc=com",
    search_filter=f"(&(objectClass=groupOfNames)(member=uid={username},ou=users,dc=empresa,dc=com))",
    attributes=["cn", "description", "owner"]
        
)


for entry in conn.entries:
    print("Entry:", entry)
    print("Owner:", entry.entry_attributes_as_dict.get("owner", [""])[0].split(",")[0].split("=")[1])
    
#print("Entries:", conn.entries)

#docker cp /home/fabiana_linux/Documentos/data-master/50-bootstrap.ldif data-master-ldap-1:/tmp/bootstrap.ldif


#docker exec data-master-ldap-1 ldapadd \
  #x \
  #H ldap://localhost:389 \
  #D "cn=admin,dc=empresa,dc=com" \
  #w admin123 \
  #f /tmp/bootstrap.ldif


#print("Entries:", conn.entries)