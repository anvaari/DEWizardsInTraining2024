import time
import random
import signal
import sys
import os
from faker import Faker
from confluent_kafka import Producer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

# Avro schema definition
schema_str = """
{
    "namespace": "example.avro",
    "type": "record",
    "name": "User",
    "fields": [
        {"name": "name", "type": "string"},
        {"name": "age", "type": "int"},
        {"name": "email", "type": "string"}
    ]
}
"""

# Initialize Faker for generating fake data
fake = Faker()

# Schema Registry configuration
schema_registry_url = os.getenv('SCHEMA_REGISTRY_URL', 'http://localhost:8081')
schema_registry_conf = {'url': schema_registry_url}

# Handle possible initialization errors
try:
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
except Exception as e:
    print(f"Failed to connect to schema registry: {e}")
    sys.exit(1)

# Avro serializer
def user_to_dict(user, ctx):
    """
    Convert User instance to dictionary.
    """
    return {
        "name": user["name"],
        "age": user["age"],
        "email": user["email"]
    }

try:
    avro_serializer = AvroSerializer(schema_registry_client, schema_str, user_to_dict)
except Exception as e:
    print(f"Failed to create AvroSerializer: {e}")
    sys.exit(1)

# Kafka producer configuration
producer_conf = {'bootstrap.servers': 'kafka1:9092,kafka2:9094,kafka3:9096'}

# Handle possible initialization errors
try:
    producer = Producer(producer_conf)
except Exception as e:
    print(f"Failed to create Kafka producer: {e}")
    sys.exit(1)

# String serializer for the key
string_serializer = StringSerializer('utf_8')

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def produce_fake_data():
    while True:
        try:
            # Generate fake data
            fake_data = {
                "name": fake.name(),
                "age": random.randint(18, 80),
                "email": fake.email()
            }

            # Produce data to Kafka topic 'users'
            producer.produce(
                topic='users',
                key=string_serializer(fake_data["name"], SerializationContext('users', MessageField.KEY)),
                value=avro_serializer(fake_data, SerializationContext('users', MessageField.VALUE)),
                on_delivery=delivery_report
            )
            producer.poll(0)

            print(f"Produced: {fake_data}")

            # Wait for 1 second
            time.sleep(1)
        except KeyboardInterrupt:
            print("Terminating...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

def shutdown_handler(signum, frame):
    print("Flushing producer...")
    producer.flush()
    sys.exit(0)

# Set up signal handling for graceful shutdown
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == "__main__":
    produce_fake_data()

