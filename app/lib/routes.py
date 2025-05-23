from flask import request, jsonify
from lib.handlers import (
    process_alertmanager_payload,
    process_pod_alert_payload,
    process_text_payload
)

def register_routes(app):
    @app.route('/api/text-to-speech', methods=['POST'])
    def text_to_speech():
        data = request.json
        app.logger.info(f"Request received with data: {data}")

        if isinstance(data, dict) and 'alerts' in data:
            return process_alertmanager_payload(data)
        elif isinstance(data, list) and all('labels' in a and 'annotations' in a for a in data):
            return process_pod_alert_payload(data)
        elif data and ('text' in data or 'msg' in data):
            return process_text_payload(data)

        app.logger.error("Invalid payload received")
        return jsonify({"error": "Invalid payload format"}), 400
