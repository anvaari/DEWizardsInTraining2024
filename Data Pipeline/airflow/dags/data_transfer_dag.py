from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from kafka import KafkaConsumer

def consume_messages():
    consumer = KafkaConsumer(
        'customer_db.customer_table',
        bootstrap_servers='kafka:9092',
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='airflow-group'
    )
    for message in consumer:
        print(message.value)

with DAG('debezium_to_airflow',
         start_date=datetime(2023, 1, 1),
         schedule_interval='@once',
         catchup=False) as dag:

    consume_task = PythonOperator(
        task_id='consume_messages',
        python_callable=consume_messages
    )

    consume_task
