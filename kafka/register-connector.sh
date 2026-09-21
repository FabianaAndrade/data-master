#!/bin/bash
# -----------------------------------------------------------
# Aguarda o Kafka Connect ficar disponível e registra o
# connector Debezium para CDC da tabela outbox.
# -----------------------------------------------------------

CONNECT_URL="http://kafka-connect:8083"
CONNECTOR_CONFIG="/connector/register-connector.json"

echo "Aguardando Kafka Connect em $CONNECT_URL ..."

until curl -s "$CONNECT_URL/connectors" > /dev/null 2>&1; do
  sleep 3
done

echo "Kafka Connect disponível!"

# Verifica se o connector já existe
EXISTING=$(curl -s "$CONNECT_URL/connectors" | grep -o '"ingestions-connector"')

if [ -n "$EXISTING" ]; then
  echo "Connector 'ingestions-connector' já existe. Atualizando config..."
  curl -s -X PUT \
    -H "Content-Type: application/json" \
    --data @"$CONNECTOR_CONFIG" \
    "$CONNECT_URL/connectors/ingestions-connector/config" | head -c 500
else
  echo "🚀 Registrando connector 'ingestions-connector'..."
  curl -s -X POST \
    -H "Content-Type: application/json" \
    --data @"$CONNECTOR_CONFIG" \
    "$CONNECT_URL/connectors" | head -c 500
fi

echo ""
echo "Status dos connectors:"
curl -s "$CONNECT_URL/connectors/ingestions-connector/status" | python3 -m json.tool 2>/dev/null || \
  curl -s "$CONNECT_URL/connectors/ingestions-connector/status"

echo ""
echo "Registro concluído!"
