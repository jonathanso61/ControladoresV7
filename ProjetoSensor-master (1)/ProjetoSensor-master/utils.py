from cassandra.cluster import Cluster

def connect_cassandra(node='172.18.0.3'):
    cluster = Cluster([node])
    session = cluster.connect('sensor_data')
    return session

