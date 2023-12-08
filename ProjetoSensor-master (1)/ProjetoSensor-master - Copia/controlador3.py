import paho.mqtt.client as mqtt
from pymongo import MongoClient
from cryptography.fernet import Fernet
import uuid

broker_address = "localhost"
port = 1883
sensor_topic = "sensor/movimento"
atuador_topic = "atuador/status"
backup_topic = "atuador/status/backup"

# Configurações do MongoDB
mongo_uri = 'mongodb://localhost:27017/'
mongo_client = MongoClient(mongo_uri)
mongo_db_primary = mongo_client['primary_database']
mongo_db_secondary = mongo_client['secondary_database']

# Chave Fernet
chave_criptografia = 'iHvA9hoWIqDc3uY9Vm8rgkNbSI5EwM-kscH7Ug-UVi4='.encode()
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

    print(f"Controlador 3 - Valor recebido: {valor}")
    dados_recebidos += 1

    valor_criptografado = cipher.encrypt(str(valor).encode())
    client.publish(atuador_topic, valor_criptografado)
    print(f"Controlador 3 - Valor publicado: {valor_criptografado}")
    client.publish(backup_topic, valor_criptografado)

    salvar_dados(valor)

def salvar_dados(valor):
    # Gerar um _id único usando UUID
    doc_id = str(uuid.uuid4())

    # Salvar dados no banco de dados principal
    try:
        mongo_db_primary.sensor_data.insert_one({'_id': doc_id, 'movimento_key': valor})
    except:
        print(f"Documento com _id {doc_id} já existe no banco de dados principal")

    # Salvar dados no banco de dados secundário
    try:
        mongo_db_secondary.sensor_data.insert_one({'_id': doc_id, 'movimento_key': valor})
    except:
        print(f"Documento com _id {doc_id} já existe no banco de dados secundário")

    # Sincronizar dados entre os bancos
    sincronizar_bancos()

def sincronizar_bancos():
    primary_data = list(mongo_db_primary.sensor_data.find())
    secondary_data = list(mongo_db_secondary.sensor_data.find())

    # Garante que ambos os bancos tenham os mesmos dados
    for data in primary_data:
        if data not in secondary_data:
            # Verifica se o documento com o mesmo _id existe no banco de dados secundário
            existing_doc = mongo_db_secondary.sensor_data.find_one({'_id': data['_id']})
            if not existing_doc:
                try:
                    mongo_db_secondary.sensor_data.insert_one(data)
                except:
                    print(f"Documento com _id {data['_id']} já existe no banco de dados secundário")

    for data in secondary_data:
        if data not in primary_data:
            # Verifica se o documento com o mesmo _id existe no banco de dados primário
            existing_doc = mongo_db_primary.sensor_data.find_one({'_id': data['_id']})
            if not existing_doc:
                try:
                    mongo_db_primary.sensor_data.insert_one(data)
                except:
                    print(f"Documento com _id {data['_id']} já existe no banco de dados principal")

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker_address, port, 60)

    client.loop_forever()
