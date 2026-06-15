# mqtt_config.py
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
WS_PORT = 9001

MQTT_SENSOR_TOPIC = "house/1/room/kitchen/sensor/gas"

MQTT_ALERT_TOPIC = "house/{house_id}/alerts"

HUB_TOPIC = "hub/{hub_id}/sensor/{sensor_type}/{sensor_id}"
BACKEND_SUB_TOPIC ="hub/+/sensor/+/+"
BACKEND_PUB_TOPIC ="client/{client_id}/hub/{hub_id}/sensor/{sensor_type}/{sensor_id}"
MQTT_TOPIC = "client/+/hub/+/sensor/+/+"  #for fronntend

HUB_ARMED_DISARMED = "hub/{hub_id}/command/security"

# HUB_TOPIC = "hub/{hub_id}/data"    #hub subscribe this and sends data to this topic


MQTT_SYS_TOPIC_CONNECTED = "$SYS/broker/clients/+/connected"
MQTT_SYS_TOPIC_DISCONNECTED = "$SYS/broker/clients/+/disconnected"