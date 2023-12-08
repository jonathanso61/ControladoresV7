import paho.mqtt.client as mqtt
from cassandra.cluster import Cluster
from cryptography.fernet import Fernet

broker_address = "localhost"
port = 1883
sensor_topic = "sensor/movimento"
atuador_topic = "atuador/status"
backup_topic = "atuador/status/backup"

# Configurações do Cassandra
cassandra_contact_points = ['cassandra1', 'cassandra2']  # Alterado para incluir ambos os nós
cassandra_keyspace = 'sensor_data'

# Chave Fernet
chave_criptografia = 'Ac9paoetI6VcL6ZleVmDNz6zB5cNwvuiGkGzDzOKcwg='.encode()
cipher = Fernet(chave_criptografia)

dados_recebidos = 0

def connect_cassandra(node):
    try:
        cluster = Cluster(contact_points=[node])
        session = cluster.connect(keyspace=cassandra_keyspace)
        return session
    except Exception as e:
        print(f"Falha na conexão com o Cassandra ({node}): {e}")
        return None

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado ao servidor MQTT")
        client.subscribe(sensor_topic)
    else:
        print(f"Falha na conexão ao servidor MQTT com código de retorno {rc}")

def on_message(client, userdata, msg):
    global dados_recebidos
    mensagem_criptografada = msg.payload
    valor_descriptografado = cipher.decrypt(mensagem_criptografada).decode()
    valor = int(valor_descriptografado)

    print(f"Controlador 1 - Valor recebido: {valor}")
    dados_recebidos += 1

    valor_criptografado = cipher.encrypt(str(valor).encode())
    client.publish(atuador_topic, valor_criptografado)
    print(f"Controlador 1 - Valor publicado: {valor_criptografado}")
    client.publish(backup_topic, valor_criptografado)

    cassandra_session = connect_cassandra('cassandra1')
    if cassandra_session:
        cassandra_session.execute(f"INSERT INTO sensor (movimento_key) VALUES ({valor})")

    sync_with_secondary_cassandra(valor)

def sync_with_secondary_cassandra(valor):
    secondary_cassandra_session = connect_cassandra('cassandra2')
    if secondary_cassandra_session:
        secondary_cassandra_session.execute(f"INSERT INTO sensor (movimento_key) VALUES ({valor})")

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker_address, port, 60)

    client.loop_forever()

