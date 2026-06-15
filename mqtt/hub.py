
import json
import os
import sys

# Go 3 levels up from hub.py to reach project root
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.append(BASE_DIR)
# PROJECT_ROOT = r"D:\MEXEMAI\IoT Camera streaming platform with MQTT\IOTstreaming"
# sys.path.append(PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "IOTstreaming.settings")

# import django

# django.setup()

import threading
import time
from datetime import datetime

import paho.mqtt.client as mqtt
from django.utils.timezone import make_aware

from IOT.firebase.firebase_notification import send_notification
from IOT.models import Device, SensorReading

MQTT_BROKER = "127.0.0.1"
WS_PORT = 9001
BACKEND_SUB_TOPIC ="hub/+/sensor/+/+"
BACKEND_PUB_TOPIC ="client/{client_id}/hub/{hub_id}/sensor/{sensor_type}/{sensor_id}"
ARM_DISARM_TPIC = "hub/+/command/security"


alerts = []

THRESHOLDS = {
    "LPG": 100,
    "Smoke": 500,
    "Fire": 500,
    "Motion_detection": 500,
    "Human_appearance": 500,
    "Door_window": 100,
}


# --------------------------------------------------
# SAVE SENSOR DATA  IN DB
# --------------------------------------------------

def save_sensor_reading(final_data):
    try:
        # hub/device check
        device = Device.objects.get(id=final_data["hub_id"])
    except Device.DoesNotExist:
        # print("No dive found, save skip")
        return
    
    timestamp = make_aware(datetime.fromtimestamp(final_data["timestamp"]))
    
    SensorReading.objects.create(
        device=device,
        sensor_id=final_data["sensor_id"],
        sensor_name = final_data["sensor_type"],
        value = final_data["value"],
        status_type = final_data["type"],
        timestamp=timestamp
    )
    

# --------------------------------------------------
# MQTT MESSAGE HANDLER
# --------------------------------------------------
# def on_message(client, userdata, msg):
#     # print("📥 BACKEND RECEIVED:", msg.topic, msg.payload)
    
#     topic = msg.topic
    
#     # ARM DISRARM 
#     if topic.startswih("hub/") and "/command/security" in topic:
#         parts = topic.split('/')
#         hub_id = parts[1]
        
#         try:
#             device = Device.objects.get(id=hub_id)
#         except Device.DoesNotExist:
#             return
        
#         payload = json.loads(msg.payload.decode())
#         action = payload.get("action")
#         if action == "arm":
#             device.armed = True
#         elif action == "disarm":
#             device.armed = False
        
#         device.save()
#         print(f"Device {hub_id} status {device.armed}")
        
            

#     try:
#         # topic: hub/{hub_id}/sensor/{sensor_type}/{sensor_id}
#         parts = topic.split("/")
#         hub_id = parts[1]
#         sensor_type = parts[3]
#         sensor_id = parts[4]
#     except Exception:
#         # print("⚠ Invalid topic format:", msg.topic)
#         return

#     payload = msg.payload.decode()
    
#     # ----------------------------
#     # CLIENT ON OF HUB
#     # ----------------------------
    
#     device = Device.objects.get(id=hub_id)
#     if not device:
#         # print("NO HUB FOUND THIS ID")
#         return
#     client_id_id = device.owner.id
#     # print("client of device:",client_id_id)


#     # ----------------------------
#     # Parse payload
#     # ----------------------------
#     try:
#         if payload.startswith("{"):
#             data = json.loads(payload)
#             value = int(data.get("value", 0))
#         else:
#             value = int(payload)
#             data = {}
#     except Exception as e:
#         print("⚠ Payload parse failed:", e)
#         return

#     # ----------------------------
#     # Determine alert type
#     # ----------------------------
#     alert_type = "alert" if (
#         sensor_type in THRESHOLDS and value > THRESHOLDS[sensor_type]
#     ) else "normal"
    
#     # print(f"Received sensor: {sensor_type}, value: {value}, threshold: {THRESHOLDS.get(sensor_type)}, alert_type: {alert_type}", flush=True)


#     # ----------------------------
#     # Build final payload
#     # ----------------------------
#     final_data = {
#         "hub_id": hub_id,
#         "sensor_id": sensor_id,
#         "sensor_type": sensor_type,
#         "value": value,
#         "type": alert_type,
#         "timestamp": int(time.time()),
#         "source": "backend",
#     }

#     alerts.append(final_data)
#     # call auto save function
#     save_sensor_reading(final_data)

#     # ----------------------------
#     # Publish to client topic
#     # ----------------------------
#     # You’ll later replace client_id with DB lookup
#     client_id = client_id_id

#     publish_topic = BACKEND_PUB_TOPIC.format(
#         client_id=client_id,
#         hub_id=hub_id,
#         sensor_type=sensor_type,
#         sensor_id=sensor_id,
#     )

#     client.publish(publish_topic, json.dumps(final_data), qos=1)
#     # print(f"📤 Published to {publish_topic}: {final_data}")
#     if alert_type == "alert":
#         # print(f"⚠️ Alert triggered for user_id={device.owner.id}", flush=True)
#         # call send_notification using owner_id
#         send_notification(user_id=device.owner.id,
#                           title=f"{sensor_type.upper()} ALERT",
#                           body=f"{sensor_type} value crossed threshold: {value}")




def on_message(client, userdata, msg):
    # print("📥 BACKEND RECEIVED:", msg.topic, msg.payload)

    topic = msg.topic

    # --------------------------------------------------
    # ARM / DISARM SECURITY COMMAND
    # --------------------------------------------------
    if topic.startswith("hub/") and "/command/security" in topic:
        try:
            parts = topic.split('/')
            hub_id = parts[1]

            device = Device.objects.get(id=hub_id)
        except Device.DoesNotExist:
            return
        except Exception:
            return

        try:
            payload = json.loads(msg.payload.decode())
            action = payload.get("action")
        except Exception:
            return

        if action == "arm":
            device.armed = True
            # print("device armed")
        elif action == "disarm":
            device.armed = False
            # print("device disarmed")
        else:
            return  # invalid action

        device.save()
        print(f"Device {hub_id} status {device.armed}")

        return  # <---- important: do not process as sensor message

    # --------------------------------------------------
    # SENSOR MESSAGE HANDLING
    # --------------------------------------------------
    try:
        # topic: hub/{hub_id}/sensor/{sensor_type}/{sensor_id}
        parts = topic.split("/")
        hub_id = parts[1]
        sensor_type = parts[3]
        sensor_id = parts[4]
    except Exception:
        return

    payload = msg.payload.decode()

    # CLIENT OWNER OF HUB
    try:
        device = Device.objects.get(id=hub_id)
    except Device.DoesNotExist:
        return

    client_id_id = device.owner.id

    # PARSE PAYLOAD
    try:
        if payload.startswith("{"):
            data = json.loads(payload)
            value = int(data.get("value", 0))
        else:
            value = int(payload)
            data = {}
    except Exception as e:
        print("⚠ Payload parse failed:", e)
        return

    # ALERT DETECTION
    alert_type = "alert" if (
        sensor_type in THRESHOLDS and value > THRESHOLDS[sensor_type]
    ) else "normal"

    final_data = {
        "hub_id": hub_id,
        "sensor_id": sensor_id,
        "sensor_type": sensor_type,
        "value": value,
        "type": alert_type,
        "timestamp": int(time.time()),
        "source": "backend",
    }

    alerts.append(final_data)
    save_sensor_reading(final_data)

    # PUBLISH TO CLIENT
    if device.armed:
        publish_topic = BACKEND_PUB_TOPIC.format(
            client_id=client_id_id,
            hub_id=hub_id,
            sensor_type=sensor_type,
            sensor_id=sensor_id,
        )

        client.publish(publish_topic, json.dumps(final_data), qos=1)

        if alert_type == "alert":
            send_notification(
                user_id=device.owner.id,
                title=f"{sensor_type.upper()} ALERT",
                body=f"{sensor_type} value crossed threshold: {value}"
            )
    else:
        print(f"Device {hub_id} is disarmed → data only saved (no publish)")


# --------------------------------------------------
# MQTT WORKER
# --------------------------------------------------
def mqtt_worker():
    client = mqtt.Client(
        transport="websockets",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )

    client.on_message = on_message

    def on_connect(client, userdata, flags, reasonCode, properties):
        # print("✅ Backend connected, reasonCode:", reasonCode)
        client.subscribe(BACKEND_SUB_TOPIC)
        client.subscribe(ARM_DISARM_TPIC)
        # print(f"✅ Subscribed to {BACKEND_SUB_TOPIC}")

    def on_disconnect(client, userdata, reasonCode, properties,packet_from_broker):
        print("⚠ Backend disconnected:", reasonCode)
        while True:
            try:
                client.reconnect()
                print("♻️ Backend reconnected")
                break
            except:
                time.sleep(1)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    client.connect(MQTT_BROKER, WS_PORT, keepalive=60)
    client.loop_forever()


# --------------------------------------------------
# START HUB
# --------------------------------------------------
def start_mqtt_hub():
    # print("🚀 Starting Backend MQTT Hub...")
    threading.Thread(target=mqtt_worker, daemon=True).start()
