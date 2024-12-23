import logging
from flask import Flask, request, jsonify
import threading
import os
import re
import pika
import json

# Configure logging at INFO level
logging.basicConfig(level=logging.INFO)

# Disable debug logs from pika, setting it to WARNING or higher
logging.getLogger("pika").setLevel(logging.WARNING)

# Load RabbitMQ settings from environment variables
rabbitmq_host = os.getenv('RABBITMQ_HOST', '')
rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
rabbitmq_vhost = os.getenv('RABBITMQ_VHOST', '')
rabbitmq_user = os.getenv('RABBITMQ_USER', '')
rabbitmq_pass = os.getenv('RABBITMQ_PASS', '')

app = Flask(__name__)

def declare_queues():
    """Function to declare the necessary queues when starting Flask."""
    # Connect to RabbitMQ
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    parameters = pika.ConnectionParameters(
        host=rabbitmq_host,
        port=rabbitmq_port,
        virtual_host=rabbitmq_vhost,
        credentials=credentials
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Declare the queues to ensure they exist
    queues = ['00_syrin_notification_warning', '00_syrin_notification_critical']
    for queue in queues:
        channel.queue_declare(queue=queue, durable=True)
        logging.info(f"Queue '{queue}' checked or created.")
    connection.close()

def send_text_to_queue(text, level):
    """Send text to RabbitMQ queue."""
    try:
        logging.info(f"Attempting to send message to RabbitMQ. Text: {text}, Level: {level}")
        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        parameters = pika.ConnectionParameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            virtual_host=rabbitmq_vhost,
            credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Construct the message in JSON format
        message = json.dumps({"text": text, "level": level})
        logging.info(f"Publishing message to queue: 00_syrin_notification_{level}")
        
        channel.basic_publish(
            exchange='',
            routing_key=f'00_syrin_notification_{level}',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Makes the message persistent
            )
        )
        logging.info("Message published successfully.")
    except Exception as e:
        logging.error(f"Error while sending message to RabbitMQ: {e}")
    finally:
        if connection and not connection.is_closed:
            connection.close()
            logging.info("RabbitMQ connection closed.")

def process_alertmanager_payload(data):
    """Process Alertmanager payload."""
    for alert in data['alerts']:
        infra = alert.get('labels', {}).get('cluster', 'PRODUCTION')
        infra = infra[0].upper() + infra[1:] if infra else ''  # Capitaliza a primeira letra
        namespace = alert.get('labels', {}).get('namespace', 'PRODUCTION')
        description = alert.get('annotations', {}).get('description', 'No description provided')
        description = description.strip()  # Remove espaços no início e no fim
        description_cleaned = re.sub(r':', ': ', description)
        description_cleaned = re.sub(r'_', '-', description_cleaned)
        text = f"[{infra}]\nNamespace: {namespace}\n{description_cleaned}"

        # Obter a severidade e mapear para 'warning' ou 'critical'
        severity = alert.get('labels', {}).get('severity', 'warning').lower()
        if severity in ['error', 'critical']:
            level = 'critical'
        else:
            level = 'warning'
            
        threading.Thread(target=send_text_to_queue, args=(text, level)).start()
    return jsonify({"message": "Alerts from Alertmanager processed successfully"}), 200

def process_pod_alert_payload(data):
    """Process pod alerts payload."""
    for alert in data:
        infra = alert.get('labels', {}).get('cluster', 'PRODUCTION')
        infra = infra[0].upper() + infra[1:] if infra else ''  # Capitaliza a primeira letra
        namespace = alert.get('labels', {}).get('namespace', 'PRODUCTION')
        description = alert.get('annotations', {}).get('description', 'No description provided')
        description = description.strip()  # Remove espaços no início e no fim
        description_cleaned = re.sub(r':', ': ', description)
        description_cleaned = re.sub(r'_', '-', description_cleaned)
        text = f"[{infra}]\nNamespace: {namespace}\n{description_cleaned}"
        
        # Obter a severidade e mapear para 'warning' ou 'critical'
        severity = alert.get('labels', {}).get('severity', 'warning').lower()
        if severity in ['error', 'critical']:
            level = 'critical'
        else:
            level = 'warning'
            
        threading.Thread(target=send_text_to_queue, args=(text, level)).start()
    return jsonify({"message": "Pod alerts processed successfully"}), 200

def process_text_payload(data):
    """Process generic text or msg payload."""
    if 'text' in data:
        text = data['text']
        field_source = 'text'
        level = "warning"
    elif 'msg' in data:  # uptime-kuma
        text = data['msg']
        field_source = 'msg'
        level = "critical"
    else:
        return jsonify({"critical": "No text field provided"}), 400

    # Process the text in a separate thread
    threading.Thread(target=send_text_to_queue, args=(text, level)).start()

    # Respond immediately that the processing has been queued
    return jsonify({"message": f"Request received from field '{field_source}', processing in progress."}), 200

@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    """Main route to handle incoming payloads."""
    data = request.json
    app.logger.info(f"Request received with data: {data}")

    if isinstance(data, dict) and 'alerts' in data:
        return process_alertmanager_payload(data)

    if isinstance(data, list) and all('labels' in alert and 'annotations' in alert for alert in data):
        return process_pod_alert_payload(data)

    if data and ('text' in data or 'msg' in data):
        return process_text_payload(data)

    app.logger.error("Invalid payload received")
    return jsonify({"error": "Invalid payload format"}), 400

declare_queues()