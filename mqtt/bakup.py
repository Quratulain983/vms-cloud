# hub.py
# import json
# import threading

# import paho.mqtt.client as mqtt

# from .config import *

# # Global list to store alerts
# alerts = []

# # Sensor thresholds
# THRESHOLDS = {
#     "gas": 400,
#     "temp": 50,
#     "smoke": 1
# }

# def on_message(client, userdata, msg):
#     """
#     Callback for when a message is received from MQTT broker.
#     Parses topic and payload, checks thresholds, and publishes alert.
#     """
#     print("📥 HUB RECEIVED:", msg.topic, msg.payload)

#     # Parse topic: house/1/room/kitchen/sensor/gas
#     try:
#         topic_parts = msg.topic.split("/")
#         house_id = topic_parts[1]
#         room = topic_parts[3]
#         sensor = topic_parts[5]
#     except IndexError:
#         print("⚠️ Invalid topic format:", msg.topic)
#         return

#     # Parse value
#     try:
#         value = int(msg.payload.decode())
#     except ValueError:
#         print("⚠️ Invalid payload, not an integer:", msg.payload)
#         return

#     # Determine alert type
#     message_type = "alert" if sensor in THRESHOLDS and value > THRESHOLDS[sensor] else "normal"

#     # Create alert data
#     data = {
#         "house": house_id,
#         "room": room,
#         "sensor": sensor,
#         "value": value,
#         "type": message_type,
#         "source": "hub"  # optional field for testing/debug
#     }

#     # Save to local list
#     alerts.append(data)

#     # Publish to client topic
#     alert_topic = MQTT_SENSOR_TOPIC.format(house_id=house_id)
#     client.publish(alert_topic, json.dumps(data), qos=1)
#     print(f"📤 Published to {alert_topic}: {data}")

# def mqtt_worker():
#     """
#     Main MQTT worker thread. Connects to broker and subscribes to topics.
#     """
#     client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
#     client.on_message = on_message

#     # Connect to broker
#     client.connect(MQTT_BROKER, MQTT_PORT)
#     print(f"✅ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")

#     # Subscribe to sensor topics
#     client.subscribe(MQTT_SENSOR_TOPIC)
#     print(f"✅ Subscribed to topic: {MQTT_SENSOR_TOPIC}")

#     # Start loop forever
#     client.loop_forever()

# def start_mqtt_hub():
#     """
#     Start MQTT hub in a background thread.
#     """
#     print('hub start')
#     thread = threading.Thread(target=mqtt_worker, daemon=True)
#     thread.start()
# ==========================================================================
# ==========================================================================
# ==========================================================================
# ==========================================================================
# ==========================================================================
# ==========================================================================
# ==========================================================================
# ==========================================================================
# import json
# import threading
# import time

# import paho.mqtt.client as mqtt

# from .config import *

# alerts = []

# THRESHOLDS = {
#     "gas": 400,
#     "temp": 50,
#     "smoke": 1
# }

# def on_message(client, userdata, msg):
#     print("📥 HUB RECEIVED:", msg.topic, msg.payload)
#     try:
#         payload = msg.payload.decode()
#         # JSON payload
#         if payload.startswith("{"):
#             data = json.loads(payload)
#             value = int(data.get("value", 0))
#         else:
#             # Raw integer
#             value = int(payload)
#             topic_parts = msg.topic.split("/")
#             data = {
#                 "house": topic_parts[1],
#                 "room": topic_parts[3],
#                 "sensor": topic_parts[5],
#                 "value": value,
#                 "type": "normal",
#                 "source": "hub"
#             }
#     except Exception as e:
#         print("⚠ Failed to parse payload:", e)
#         return

#     # Determine alert type
#     data["type"] = "alert" if data["sensor"] in THRESHOLDS and value > THRESHOLDS[data["sensor"]] else "normal"
#     data["source"] = "hub"

#     alerts.append(data)

#     # Publish processed alert
#     alert_topic = MQTT_ALERT_TOPIC.format(house_id=data["house"])
#     client.publish(alert_topic, json.dumps(data), qos=1)
#     print(f"📤 Published to {alert_topic}: {data}")


# def mqtt_worker():
#     client = mqtt.Client(
#         transport="websockets",
#         callback_api_version=mqtt.CallbackAPIVersion.VERSION2
#     )

#     client.on_message = on_message

#     # Correct VERSION2 callback signature
#     def on_connect(client, userdata, flags, reasonCode, properties):
#         print("✅ Connected to broker, reasonCode=", reasonCode)
#         client.subscribe(MQTT_SENSOR_TOPIC)
#         print(f"✅ Subscribed to: {MQTT_SENSOR_TOPIC}")

#     def on_disconnect(client, userdata, reasonCode, properties):
#         print("⚠ MQTT disconnected, reasonCode=", reasonCode)
#         if reasonCode != 0:
#             # Non-blocking reconnect
#             while True:
#                 try:
#                     client.reconnect()
#                     print("♻️ Reconnected to broker")
#                     break
#                 except Exception as e:
#                     print("❌ Reconnect failed:", e)
#                     time.sleep(1)

#     client.on_connect = on_connect
#     client.on_disconnect = on_disconnect

#     # Connect to WebSocket broker
#     client.connect(MQTT_BROKER, 9001, keepalive=60)

#     # Non-blocking loop to prevent thread freeze
#     client.loop_start()

#     # Keep the thread alive
#     while True:
#         time.sleep(1)


# def start_mqtt_hub():
#     print("🚀 Starting MQTT hub...")
#     thread = threading.Thread(target=mqtt_worker, daemon=True)
#     thread.start()
# ===================================================================
# ===================================================================
# ===================================================================
# ===================================================================
# ===================================================================
# ===================================================================
# ===================================================================






# test_hub publisher
# import json
# import random
# import time

# import paho.mqtt.client as mqtt

# MQTT_BROKER = "127.0.0.1"
# MQTT_PORT = 1883
# MQTT_TOPIC = "house/1/room/kitchen/sensor/gas"

# HOUSE_ID = 1
# ALERT_TOPIC = f"house/{HOUSE_ID}/alerts"

# client = mqtt.Client()
# client.connect(MQTT_BROKER, MQTT_PORT)  # 1883
# print("TCP test publisher connected")

# # client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
# # client.connect(MQTT_BROKER, MQTT_PORT)  # 1883



# print("🚀 Test Hub Publisher started...")

# while True:
#     payload = {
#         "house": HOUSE_ID,
#         "room": "kitchen",
#         "sensor": "gas",
#         "value": random.randint(200, 600),
#         "type": random.choice(["normal", "alert"]),
#         "source": "hub-test"
#     }

#     payload_json = json.dumps(payload)
#     client.publish(ALERT_TOPIC, payload_json, qos=1)
#     print(f"📤 Published to {ALERT_TOPIC}: {payload_json}")

#     time.sleep(0.5)
# ============================================================
# ============================================================
# ============================================================
# ============================================================
# ============================================================
# ============================================================
# ============================================================
# ============================================================




# import json
# import random
# import time

# import paho.mqtt.client as mqtt

# MQTT_BROKER = "127.0.0.1"
# MQTT_PORT = 9001
# MQTT_TOPIC = "house/1/room/kitchen/sensor/gas"


# client = mqtt.Client(transport="websockets", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
# client.connect(MQTT_BROKER, MQTT_PORT)
# client.loop_start()

# while True:
#     value = random.randint(200, 600)
#     client.publish(MQTT_TOPIC, str(value), qos=1)
#     print(f"📤 Published: {value}")
#     time.sleep(30)



# ============================================================
# ============================================================
# ============================================================
# ============================================================
# ============================================================
# ============================================================
# ============================================================
# ============================================================


