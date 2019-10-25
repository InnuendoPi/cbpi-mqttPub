# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
from eventlet import Queue
from modules import cbpi, app, ActorBase
from modules.core.hardware import SensorActive
import json
import os
import re
import threading
import time
from modules.core.props import Property

q = Queue()


def on_connect(client, userdata, flags, rc):
    print("MQTT Connected" + str(rc))


class MQTTThread (threading.Thread):

    def __init__(self, server, port, username, password, tls):
        threading.Thread.__init__(self)
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.tls = tls

    client = None

    def run(self):
        self.client = mqtt.Client()
        self.client.on_connect = on_connect

        if self.username != "username" and self.password != "password":
            self.client.username_pw_set(self.username, self.password)

        if self.tls.lower() == 'true':
            self.client.tls_set_context(context=None)

        self.client.connect(str(self.server), int(self.port), 60)
        self.client.loop_forever()


@cbpi.initalizer(order=0)
def initMQTT(app):

    server = app.get_config_parameter("MQTT_SERVER", None)
    if server is None:
        server = "localhost"
        cbpi.add_config_parameter(
            "MQTT_SERVER", "localhost", "text", "MQTT Server")

    port = app.get_config_parameter("MQTT_PORT", None)
    if port is None:
        port = "1883"
        cbpi.add_config_parameter(
            "MQTT_PORT", "1883", "text", "MQTT Sever Port")

    username = app.get_config_parameter("MQTT_USERNAME", None)
    if username is None:
        username = "username"
        cbpi.add_config_parameter(
            "MQTT_USERNAME", "username", "text", "MQTT username")

    password = app.get_config_parameter("MQTT_PASSWORD", None)
    if password is None:
        password = "password"
        cbpi.add_config_parameter(
            "MQTT_PASSWORD", "password", "text", "MQTT password")

    tls = app.get_config_parameter("MQTT_TLS", None)
    if tls is None:
        tls = "false"
        cbpi.add_config_parameter("MQTT_TLS", "false", "text", "MQTT TLS")

    app.cache["mqtt"] = MQTTThread(server, port, username, password, tls)
    app.cache["mqtt"].daemon = True
    app.cache["mqtt"].start()


@cbpi.backgroundtask(key='mqtt_pub', interval=30)
def mqtt_pub(api):
    """
    background process that reads all passive sensors in interval of 5 second
    :return: None
    """
    for i, value in cbpi.cache['kettle'].items():
        topic = 'MQTTDevice/kettle/' + str(i)
        data = {
            'id': i,
            'name': value.name,
            'target_temp': value.target_temp
        }
        api.cache["mqtt"].client.publish(
            topic, payload=json.dumps(data, ensure_ascii=False), qos=0, retain=False)
