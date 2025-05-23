import os
import json
import pika
import logging

# Disable debug logs from pika, setting it to WARNING or higher
logging.getLogger("pika").setLevel(logging.WARNING)

rabbitmq_host = os.getenv('RABBITMQ_HOST', '')
rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
rabbitmq_vhost = os.getenv('RABBITMQ_VHOST', '')
rabbitmq_user = os.getenv('RABBITMQ_USER', '')
rabbitmq_pass = os.getenv('RABBITMQ_PASS', '')

def get_connection():
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    parameters = pika.ConnectionParameters(
        host=rabbitmq_host,
        port=rabbitmq_port,
        virtual_host=rabbitmq_vhost,
        credentials=credentials
    )
    return pika.BlockingConnection(parameters)

def declare_queues():
    connection = get_connection()
    channel = connection.channel()
    for queue in ['00_syrin_notification_warning', '00_syrin_notification_critical']:
        channel.queue_declare(queue=queue, durable=True)
        logging.info(f"Queue '{queue}' declared.")
    connection.close()

def send_text_to_queue(text, level):
    connection = None
    try:
        connection = get_connection()
        channel = connection.channel()
        message = json.dumps({"text": text, "level": level})
        channel.basic_publish(
            exchange='',
            routing_key=f'00_syrin_notification_{level}',
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        logging.info(f"Message published to {level} queue.")
    except Exception as e:
        logging.error(f"Failed to send message: {e}")
    finally:
        if connection and not connection.is_closed:
            connection.close()
