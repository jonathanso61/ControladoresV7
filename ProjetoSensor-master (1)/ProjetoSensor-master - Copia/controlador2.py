import paho.mqtt.client as mqtt
from cryptography.fernet import Fernet
from utils import connect_cassandra

broker_address = "localhost"
port = 1883
sensor_topic = "sensor/movimento"
atuador_topic = "atuador/status"
backup_topic = "atuador/status/backup"

# Chave Fernet
chave_criptografia = 'xeTK3OZ9t9FzMfrwMHBtrJb2SMyBoLVnnNGtHEIaCzQ='.encode()
cipher = Fernet(chave_criptografia)

dados_recebidos = 0

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

    print(f"Controlador 2 - Valor recebido: {valor}")

    if valor == 1:
        valor_criptografado = cipher.encrypt(str("ativado").encode())
        dados_recebidos += 1
        client.publish(atuador_topic, valor_criptografado)
        print(f"Controlador 2 - Valor publicado: {valor_criptografado}")
        client.publish(backup_topic, valor_criptografado)

        print("Antes de connect_cassandra")
        cassandra_session = connect_cassandra()
        print("Depois de connect_cassandra")
        if cassandra_session:
            cassandra_session.execute(f"INSERT INTO sensor_data.sensor (id, movimento_key) VALUES (uuid(), {valor})")

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker_address, port, 60)

    client.loop_forever()




