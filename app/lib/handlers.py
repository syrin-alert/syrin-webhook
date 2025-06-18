import os
import re
import threading
from flask import jsonify
from lib.rabbitmq import send_text_to_queue

SERVICE_K8S = os.getenv('SERVICE_K8S', 'oke')

def clean_description(description):
    description = description.strip()
    description = re.sub(r':', ': ', description)
    description = re.sub(r'_', '-', description)
    return description

def extract_alert_info(alert):
    labels = alert.get('labels', {})
    annotations = alert.get('annotations', {})

    infra = labels.get('cluster', '( unidentified )').upper()
    k8s = labels.get(SERVICE_K8S, '( unidentified )').upper()
    tenancy = labels.get('tenancy', '( unidentified )').lower() if SERVICE_K8S == 'oke' else ''
    namespace = labels.get('namespace', '( unidentified )').lower()
    nodename = labels.get('nodename', '( unidentified )').lower()
    description = clean_description(annotations.get('description', 'No description provided'))
    summary = clean_description(annotations.get('summary', 'No summary provided'))
    severity = labels.get('severity', 'warning').lower()
    level = 'critical' if severity in ['error', 'critical'] else 'warning'

    text = (
        f"Environment: {infra}\n"
        f"Tenancy: {tenancy}\n"
        f"Kubernetes: {k8s}\n"
        f"Namespace: {namespace}\n"
        f"Nodename: {nodename}\n"
        f"Description: {description}\n"
        f"Summary: {summary}"
    )

    return text, level

def process_alerts(alerts):
    for alert in alerts:
        text, level = extract_alert_info(alert)
        threading.Thread(target=send_text_to_queue, args=(text, level)).start()

def process_alertmanager_payload(data):
    process_alerts(data['alerts'])
    return jsonify({"message": "Alerts from Alertmanager processed successfully"}), 200

def process_pod_alert_payload(data):
    process_alerts(data)
    return jsonify({"message": "Pod alerts processed successfully"}), 200

def process_text_payload(data):
    if 'text' in data:
        text = data['text']
        level = "warning"
    elif 'msg' in data:
        text = data['msg']
        level = "critical"
    else:
        return jsonify({"critical": "No text field provided"}), 400

    threading.Thread(target=send_text_to_queue, args=(text, level)).start()
    return jsonify({"message": "Request received, processing in progress."}), 200
