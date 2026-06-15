
import json
import os
import random
import sys
import time

import django
import paho.mqtt.client as mqtt
from config import HUB_TOPIC, MQTT_BROKER, WS_PORT

PROJECT_ROOT = r"C:\Users\12345\Desktop\vms cloud server"
sys.path.append(PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vmscloud.settings")
django.setup()
from vms.models import Gateway, Sensor
client = mqtt.Client(
    transport="websockets",
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)


client.connect(MQTT_BROKER,WS_PORT)



client.loop_start()
print("HUB connected to Broker")


def get_sensors(hub_id):
    try:
        gateway = Gateway.objects.get(gateway_id=hub_id)
        sensors = Sensor.objects.filter(gateway=gateway)
        
        if not sensors.exists():
            print("No sensors found")
            return {}
        
        sensor_dict = {}
        for sensor in sensors:
            sensor_type = sensor.sensortype.name if sensor.sensortype else "unknown"
            if sensor_type not in sensor_dict:
                sensor_dict[sensor_type] = []
            sensor_dict[sensor_type].append({
                "id": sensor.sensor_id,
                "name": sensor.sensor_name
            })
        return sensor_dict
    
    except Gateway.DoesNotExist:
        print("Gateway not found")
        return {}

    
HUB_ID = 3
PUBLISH_INTERVAL = 5

print(f"starting the test publisherfor hub:{HUB_ID}")

while True:
    sensors = get_sensors(HUB_ID)
    print(f"Sensors found: {sensors}")
    if not sensors:
        print(f"⚠️ No sensors found for hub_id={HUB_ID}")
        time.sleep(PUBLISH_INTERVAL)
        continue

    for sensor_type, sensor_info in sensors.items():
        # sensor_info could be a dict or list (like Door_window)
        if isinstance(sensor_info, list):
            for s in sensor_info:
                sensor_id = s.get("id")
                sensor_name = s.get("name")
                topic = f"hub/{HUB_ID}/sensor/{sensor_type}/{sensor_id}"
                value = random.randint(0, 600)
                payload = json.dumps({
                    "hub_id": HUB_ID,
                    "sensor_type": sensor_type,
                    "sensor_id": sensor_id,
                    "sensor_name": sensor_name,
                    "value": value,
                    "timestamp": time.time()
                })
                client.publish(topic, payload, qos=1)
                print(f"📤 Published to {topic}: {payload}")
        else:
            sensor_id = sensor_info.get("id")
            sensor_name = sensor_info.get("name")
            topic = f"hub/{HUB_ID}/sensor/{sensor_type}/{sensor_id}"
            value = random.randint(0, 600)
            payload = json.dumps({
                "hub_id": HUB_ID,
                "sensor_type": sensor_type,
                "sensor_id": sensor_id,
                "sensor_name": sensor_name,
                "value": value,
                "timestamp": time.time()
            })
            client.publish(topic, payload, qos=1)
            # print(f"📤 Published to {topic}: {payload}")

    time.sleep(PUBLISH_INTERVAL)