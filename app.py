# coding: utf-8
import datetime
import json
import threading
from time import sleep

from flask import Flask, request, abort

import api
import threading

app = Flask(__name__)
app.config['DEBUG'] = True

TABLE_LAMP = 'abbdc9e1-716d-4778-a3b3-e4ca073e9734'
WARDROBE = '95471d1e-2d08-4ded-a5f5-2c99bae24f10'
SOCKET = 'eb18aae4-d976-4f35-abd4-7678273f7ad6'
LED = '5a057973-c03f-4b74-93bb-cb501725cece'
CHANDELIER = '88515660-2ec4-43bf-92b8-9feeed906c68'
HUMIDIFIER = '63b895d1-3e41-47c1-b81f-c5ce1cf6967c'
AIR_BLOWER = "air_blower"
PI = "pi"
SERVER_AMD = "server_wardrobe"
SERVER_VPN_FRA = "fra_vpn"

# devices = {'lamp': lamp, 'wardrobe': wardrobe, 'socket': socket, 'led': led, 'chandelier': chandelier,
#                'main_light': main_light, 'back_light': back_light, 'humidifier': humidifier, 'airfresh': air_fresh,
#                "pi": pi}

names = {
    TABLE_LAMP: {"name": "Bedside Lamp", "local_name": "lamp"},
    WARDROBE: {"name": "Wardrobe Light", "local_name": "wardrobe"},
    SOCKET: {"name": "Power Socket", "local_name": "socket"},
    LED: {"name": "LED light", "local_name": "led"},
    CHANDELIER: {"name": "Chandelier", "local_name": "chandelier"},
    HUMIDIFIER: {"name": "Humidifier", "local_name": "humidifier"},
    AIR_BLOWER: {"name": "Air Blower", "local_name": "airfresh"},
    PI: {"name": "Raspberry Pi", "local_name": "pi"},
    SERVER_AMD: {"name": "Server AMD", "local_name": "server_wardrobe"},
    SERVER_VPN_FRA: {"name": "Server VPN", "local_name": "server_vpn"}

}

BACK_LIGHT = 'a0bcbd2a-56f8-4c9e-8d3a-659bcfbd2148'
MAIN_LIGHT = '8417b6b1-3981-41e0-bf37-610c7227432c'
SCENARIO1 = 'e80a8aea-ccaf-41d3-a92a-c6ddcce9c994'

# TOKENS
TABLE_LAMP_TOKEN = "7643e32d64f1f4bfc63fccaada879b50"
TABLE_LAMP_IP = "192.168.86.93"

HUMIDIFIER_TOKEN = "4514fb07a33eb684d058509ce7789250"
HUMIDIFIER_IP = "192.168.86.34"

SOCKET_TOKEN = "2cf6b47d58b57cf751b30fca16ba00e4"
SOCKET_IP = "192.168.88.246"

SERVER_AMD_IP = "192.168.86.164:8000"

SERVER_VPN_FRA_IP = "46.101.173.157:8000"

devices = {}
scenarios = {}


def update_state_v3():
    res = api.Iot.state_v3()
    for info in res:
        try:
            info.name = names.get(info.id).get("name")
        except AttributeError:
            continue
        local_name = names.get(info.id).get("local_name")
        if info.id == CHANDELIER or info.id == WARDROBE or info.id == SOCKET:
            d = api.Switch(info)
            print(info)
            devices[local_name] = d
        elif info.id == LED:
            d = api.Light(info)
            d.get_state()
            devices[local_name] = d
        elif info.id == TABLE_LAMP:
            d = api.AdvancedLight(info, TABLE_LAMP_IP, TABLE_LAMP_TOKEN)
            d.get_state()
            devices[local_name] = d
        elif info.id == HUMIDIFIER:
            d = api.Humidifier(info)
            devices[local_name] = d

    air_fresh = api.AirBlower(names.get(AIR_BLOWER).get("local_name"), names.get(AIR_BLOWER).get("name"))
    devices[names.get(AIR_BLOWER).get("name")] = air_fresh

    pi = api.Raspberry(names.get(PI).get("local_name"), names.get(PI).get("name"))
    devices[names.get(PI).get("name")] = pi

    server = api.Server(names.get(SERVER_AMD).get("local_name"), names.get(SERVER_AMD).get("name"), SERVER_AMD_IP)
    server.get_state()
    devices[names.get(SERVER_AMD).get("name")] = server

    server_vpn = api.Server(names.get(SERVER_VPN_FRA).get("local_name"), names.get(SERVER_VPN_FRA).get("name"),
                            SERVER_VPN_FRA_IP)
    server_vpn.get_state()
    devices[names.get(SERVER_VPN_FRA).get("name")] = server_vpn


# /home/data/disk2TB/data/database/eda

# def update_state(pr=True):
#     global devices
#     global scenarios
#
#     state = api.Iot.state()
#     if pr:
#         print(state)
#     lamp = api.AdvancedLight(TABLE_LAMP, state[TABLE_LAMP], TABLE_LAMP_IP, TABLE_LAMP_TOKEN, name="Bedside Lamp")
#     lamp.get_state()
#     wardrobe = api.Switch(WARDROBE, state[WARDROBE], name="Wardrobe Light")
#     socket = api.Switch(SOCKET, state[SOCKET], name="Power Socket")
#     led = api.Light(LED, state[LED], name="LED Light")
#     led.get_state()
#     chandelier = api.Switch(CHANDELIER, state[CHANDELIER], name="Chandelier")
#     humidifier = api.Humidifier(HUMIDIFIER, state[HUMIDIFIER], name="Humidifier")
#     humidifier.update_state()
#

#     back_light = api.Light(BACK_LIGHT, state[BACK_LIGHT], is_group=True, check_state=False, children=[lamp, led],
#                            name="Back Light")
#     main_light = api.Switch(MAIN_LIGHT, state[MAIN_LIGHT], True, children=[chandelier, wardrobe], name="Main Light")
#
#     if led.state:
#         back_light.color = led.color
#         back_light.brightness = led.brightness
#     elif lamp.state:
#         back_light.color = lamp.color
#         back_light.brightness = lamp.brightness
#     else:
#         back_light.color = lamp.color
#         back_light.brightness = 0
#         back_light.state = False
#
#     sleep_scenario = api.Scenario(SCENARIO1, children=[lamp, wardrobe, socket, led, chandelier, main_light, back_light])
#     air_fresh = api.AirBlower("airfresh", "Air Blower")
#
#     pi = api.Raspberry()
#
#     devices = {'lamp': lamp, 'wardrobe': wardrobe, 'socket': socket, 'led': led, 'chandelier': chandelier,
#                'main_light': main_light, 'back_light': back_light, 'humidifier': humidifier, 'airfresh': air_fresh,
#                "pi": pi}
#
#     scenarios = {"turn_off": sleep_scenario}


def start2():
    lamp = devices.get("lamp")
    lamp.blink_color(['red'])


# start2()ч


@app.route('/devices', methods=['GET'])
def devices_f():
    res = []
    for name, device in devices.items():
        if isinstance(device, api.AdvancedLight):
            res.append({
                "name": name,
                "type": device.__class__.__name__.lower(),
                "isGroup": False,
                "userFriendlyName": device.name,
                "state": device.state,
                "brightness": device.get_brightness(),
                "rgb": device.rgb,
                "mode": device.mode
            })
        elif isinstance(device, api.Light):
            res.append({
                "name": name,
                "type": device.__class__.__name__.lower(),
                # "isGroup": device.is_group,
                "userFriendlyName": device.name,
                "state": device.state,
                "brightness": device.brightness,
                "color": device.color
            })
        elif isinstance(device, api.Humidifier):
            res.append({
                "name": name,
                "type": device.__class__.__name__.lower(),
                "userFriendlyName": device.name,
                # "isGroup": device.is_group,
                "state": device.state,
                "humidity": device.humidity,
                "temperature": device.temperature
            })
        elif isinstance(device, api.AirBlower):
            device.update_state()
            res.append({
                "name": name,
                "type": device.__class__.__name__.lower(),
                "userFriendlyName": device.name,
                "state": device.power,
                "fanLevel": device.fan_level,
                "heater": device.heater,
                "alarm": device.alarm,
                "temperature": device.temperature
            })
        elif isinstance(device, api.AbstractServer):
            res.append({
                "name": name,
                "type": device.__class__.__name__.lower(),
                "userFriendlyName": device.name,
                "temperature": device.temperature,
                "sensors": device.sensors,
                "internet": device.internet,
                "cpu": device.cpu,
                "memory": device.memory
            })

        else:
            res.append({
                "name": name,
                "type": device.__class__.__name__.lower(),
                # "isGroup": device.is_group,
                "userFriendlyName": device.name,
                "state": device.state,
            })
    return json.dumps({
        "devices": res,
        "scenarios": [{
            "name": "turn_off",
            "userFriendlyName": "Turn Off"
        }],
        "palette": devices.get("led").palette

    })


@app.route('/execute', methods=['GET'])
def execute():
    d = scenarios.get(request.args.get('device'))
    if d and isinstance(d, api.Scenario):
        return str(d.execute())
    else:
        abort(400)


@app.route('/blink', methods=['GET'])
def blink():
    d = devices.get(request.args.get('device'))
    if d and not d.is_group:
        return str(d.blink())
    else:
        abort(400)


@app.route('/room_state', methods=['GET'])
def room_state():
    humidifier = devices.get("humidifier")
    humidifier.update_state()
    s = humidifier.get_state()
    return f'humidity: {s[0]}% temperature: {s[1]}°C'


@app.route('/blink_color', methods=['GET'])
def blink_color():
    d = devices.get(request.args.get('device'))
    interval = request.args.get('interval')
    if not interval:
        interval = 0
    if d and isinstance(d, api.Light) and not d.is_group:
        return str(d.blink_color([request.args.get('color')], int(interval)))
    else:
        abort(400)


@app.route('/blink_brightness', methods=['GET'])
def blink_brightness():
    d = devices.get(request.args.get('device'))
    interval = request.args.get('interval')
    if not interval:
        interval = 0
    if d and isinstance(d, api.Light) and not d.is_group:
        d.blink_brightness([request.args.get('value')], int(interval))
        return str(True)
    else:
        abort(400)


@app.route('/set_rgb', methods=['GET'])
def set_rgb():
    d = devices.get(request.args.get('device'))
    if d and isinstance(d, api.AdvancedLight):
        rgb = (int(request.args.get('r')), int(request.args.get('g')), int(request.args.get('b')))

        return str(d.set_rbg(rgb))
    else:
        abort(400)


@app.route('/set_mode', methods=['GET'])
def set_mode():
    d = devices.get(request.args.get('device'))
    if d and isinstance(d, api.AdvancedLight):
        return str(d.change_mode(int(request.args.get('mode'))))
    else:
        abort(400)


@app.route('/turn_on', methods=['GET'])
def turn_on():
    d = devices.get(request.args.get('device'))
    print("turn_on", d)
    if d:
        return str(d.turn_on())
    else:
        abort(400)


@app.route('/turn_off', methods=['GET'])
def turn_off():
    d = devices.get(request.args.get('device'))
    print("turn_off", d)
    if d:
        return str(d.turn_off())
    else:
        abort(400)


@app.route('/set_fan_level', methods=['GET'])
def set_fan_level():
    d = devices.get(request.args.get('device'))
    if d and isinstance(d, api.AirBlower):
        return d.set_fan_level(request.args.get('speed'))
    else:
        abort(400)


@app.route('/turn_on_heat', methods=['GET'])
def turn_on_heat():
    d = devices.get(request.args.get('device'))
    if d and isinstance(d, api.AirBlower):
        return d.request('turn_on_heat')
    else:
        abort(400)


@app.route('/turn_off_heat', methods=['GET'])
def turn_off_heat():
    d = devices.get(request.args.get('device'))
    if d and isinstance(d, api.AirBlower):
        return d.request('turn_off_heat')
    else:
        abort(400)


@app.route('/turn_on_sound', methods=['GET'])
def turn_on_sound():
    d = devices.get(request.args.get('device'))
    if d and isinstance(d, api.AirBlower):
        return d.request('turn_on_sound')
    else:
        abort(400)


@app.route('/turn_off_sound', methods=['GET'])
def turn_off_sound():
    d = devices.get(request.args.get('device'))
    if d and isinstance(d, api.AirBlower):
        return d.request('turn_off_sound')
    else:
        abort(400)


@app.route('/get_state', methods=['GET'])
def get_state():
    d = devices.get(request.args.get('device'))
    if d:
        return json.dumps(d.get_state())
    else:
        abort(400)


@app.route('/set_brightness', methods=['GET'])
def set_brightness():
    d = devices.get(request.args.get('device'))
    print(request.args.get('value'))
    if d and isinstance(d, api.Light):
        return str(d.change_brightness(float(request.args.get('value'))))
    else:
        abort(400)


@app.route('/set_color', methods=['GET'])
def set_color():
    d = devices.get(request.args.get('device'))
    if d and isinstance(d, api.Light):
        return str(d.change_color(request.args.get('color')))
    else:
        abort(400)


def start_update():
    def regular_update_state():
        while True:
            print(datetime.datetime.now())
            sleep(30)
            try:
                update_state_v3()
            except Exception as e:
                print(e)
                with open('app.log', 'a') as f:
                    print(e, file=f)

    threading.Thread(target=regular_update_state).start()

    # app.run(debug=True, port='8000', host='0.0.0.0')
    return app


update_state_v3()
start_update()
# if __name__ == '__main__':
#     main()
    # gunicorn app:app --bind 0.0.0.0:8000 --daemon
# /usr/lib/jvm/java-1.8.0-openjdk-amd64/bin/java -Xms4G -Xmx4G -Xmn768m -XX:+AggressiveOpts -XX:+AlwaysPreTouch -XX:+DisableExplicitGC -XX:+ParallelRefProcEnabled -XX:+PerfDisableSharedMem -XX:+UseCompressedOops -XX:-UsePerfData -XX:MaxGCPauseMillis=200 -XX:ParallelGCThreads=8 -XX:ConcGCThreads=2 -XX:+UseG1GC -XX:InitiatingHeapOccupancyPercent=50 -XX:G1HeapRegionSize=1 -XX:G1HeapWastePercent=5 -XX:G1MixedGCCountTarget=8 -Dfml.readTimeout=30 -jar forge-1.16.5-36.2.20.jar
