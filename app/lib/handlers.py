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

def process_alertmanager_payload(data):
    for alert in data['alerts']:
        infra = alert.get('labels', {}).get('cluster', '(não identificado)').capitalize()
        k8s = alert.get('labels', {}).get(SERVICE_K8S, '(não identificado)').capitalize()
        if SERVICE_K8S == 'oke':
            tenancy = alert.get('labels', {}).get('tenancy', '(não identificado)').capitalize()
        namespace = alert.get('labels', {}).get('namespace', '(não identificado)')
        description = clean_description(alert.get('annotations', {}).get('description', 'No description provided'))
        text = f"Ambiente: {infra}\n Tenancy: {tenancy}\n Kubernetes: {k8s}\n Namespace: {namespace}\n{description}"
        severity = alert.get('labels', {}).get('severity', 'warning').lower()
        level = 'critical' if severity in ['error', 'critical'] else 'warning'
        threading.Thread(target=send_text_to_queue, args=(text, level)).start()
    return jsonify({"message": "Alerts from Alertmanager processed successfully"}), 200

def process_pod_alert_payload(data):
    for alert in data:
        infra = alert.get('labels', {}).get('cluster', '(não identificado)').capitalize()
        k8s = alert.get('labels', {}).get(SERVICE_K8S, '(não identificado)').capitalize()
        if SERVICE_K8S == 'oke':
            tenancy = alert.get('labels', {}).get('tenancy', '(não identificado)').capitalize()
        namespace = alert.get('labels', {}).get('namespace', '(não identificado)')
        description = clean_description(alert.get('annotations', {}).get('description', 'No description provided'))
        text = f"Ambiente: {infra}\n Tenancy: {tenancy}\n Kubernetes: {k8s}\n Namespace: {namespace}\n{description}"
        severity = alert.get('labels', {}).get('severity', 'warning').lower()
        level = 'critical' if severity in ['error', 'critical'] else 'warning'
        threading.Thread(target=send_text_to_queue, args=(text, level)).start()
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
    return jsonify({"message": f"Request received, processing in progress."}), 200
