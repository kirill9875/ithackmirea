import paho.mqtt.client as mqtt
import math
import artikcloud
from artikcloud.rest import ApiException
import pynmea2

import threading

import time

BASE_COORDS = (55.67, 37.48, 0.008)
AIM_HEIGHT = 10


class Device:

    def __init__(self, mqtt_client):

        self._mqtt_client = mqtt_client
        self._light_state = 0  # 0 - off, 1 - red, 2 - green, 3 - blue

        self._state_to_pin = [0, 25, 26, 24]

        for pin in range(24, 27):
            self._mqtt_client.publish('devices/lora/807b859020000261/gpio', f'set {pin} 0')

    def _set_light_state(self, state):
        # if self._light_state != 0:
        #    self.mqtt_client.publish('devices/lora/807b859020000261/gpio', f'set {self._state_to_pin[self._light_state]} 0')
        self._mqtt_client.publish('devices/lora/807b859020000261/gpio', f'set {self._state_to_pin[state]} 1')
        self._light_state = state

    def light_off(self):
        self._set_light_state(0)

    def set_light_color(self, color):
        color_to_state = {'r': 1, 'g': 2, 'b': 3}
        self._set_light_state(color_to_state[color])

    def set_servo_rotation(self, radians):
        min_percent = 2.77
        max_percent = 12
        duty = radians / math.pi * (max_percent - min_percent) + min_percent
        self._mqtt_client.publish('devices/lora/807b859020000261/pwm', f'set freq 50 dev 1 on ch 1 duty {duty}')
        # self._mqtt_client.publish('devices/lora/807b859020000261/pwm', 'set freq 50 dev 1 on ch 1 duty 0')

        print(f'Servo duty: {duty}')


class CloudService:

    def __init__(self):
        artikcloud.configuration.access_token = '191b9167e18d451f8cb80a19214c9164'
        self._api_instance = artikcloud.MessagesApi()

    def send_gps_data(self, long, lat):
        try:
            data = artikcloud.Message()
            data.data = {'long': long, 'lat': lat}
            data.sdid = '96bcc8a85c394cb4a8858eef1af65fae'
            self._api_instance.send_message(data)
        except ApiException as e:
            print("Exception when calling DeviceTypesApi->get_available_manifest_versions")

    def send_rotation_data(self, phi, theta):
        try:
            data = artikcloud.Message()
            data.data = {'phi': phi, 'theta': theta}
            data.sdid = '96bcc8a85c394cb4a8858eef1af65fae'
            self._api_instance.send_message(data)
        except ApiException as e:
            print("Exception when calling DeviceTypesApi->get_available_manifest_versions")


def compute_antenna_angles(base_coords, aim_coords):
    x_factor = 62.77
    y_factor = 111.11
    direction_vector_xy_km = [(aim_coords[0] - base_coords[0]) * x_factor, (aim_coords[1] - base_coords[1]) * y_factor, aim_coords[2] - base_coords[2]]
    mirror = direction_vector_xy_km[1] < 0
    if mirror:
        direction_vector_xy_km[0] = -direction_vector_xy_km[0]
        direction_vector_xy_km[1] = -direction_vector_xy_km[1]
    xy_length_km = (direction_vector_xy_km[0] ** 2 + direction_vector_xy_km[1] ** 2) ** 0.5
    phi = math.acos(direction_vector_xy_km[0] / xy_length_km)
    theta = math.atan(direction_vector_xy_km[2] / xy_length_km)
    if mirror:
        theta = math.pi - theta
    return phi, theta


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("hyrocopter/devices/gps")


def on_message(client, userdata, msg):

    print(msg.payload)
    payload_string = msg.payload.decode(encoding='utf-8')

    if payload_string.startswith('$GPGSA'):
        print('GPGSA data, ignored.')
        return

    print('GPRMC data, aiming..')

    gps_data = pynmea2.parse(payload_string)

    longitude = float(gps_data.longitude)
    latitude = float(gps_data.latitude)

    cloud.send_gps_data(longitude, latitude)
    angles = compute_antenna_angles(BASE_COORDS, (longitude, latitude, AIM_HEIGHT))

    cloud.send_rotation_data(angles[0], angles[1])
    print(f'Antenna angles: [phi: {angles[0]}, theta: {angles[1]}]')

    device.set_light_color('g')
    device.set_servo_rotation(angles[0])

    time.sleep(1)

    device.set_light_color('r')
    device.set_servo_rotation(angles[1])

    time.sleep(1)

    print('Aiming data successfully sent.')


gps_client = mqtt.Client()
gps_client.on_connect = on_connect
gps_client.on_message = on_message
gps_client.connect("10.11.162.229", 1883, 60)

device_client = mqtt.Client()
device_client.on_connect = on_connect
device_client.connect("10.11.162.100", 1883, 60)

device = Device(device_client)
cloud = CloudService()

gps_thread = threading.Thread(target=mqtt.Client.loop_forever, args=(gps_client,))
device_thread = threading.Thread(target=mqtt.Client.loop_forever, args=(device_client,))

gps_thread.start()
device_thread.start()
# device_client.loop_forever()
