import json
import typing

import psutil
import requests
import time
import threading
import logging
from miio import Yeelight
from gpiozero import CPUTemperature
import speedtest

with open('headers.json') as f:
    HEADERS = json.load(f)

COLOR_LIST = ['white', 'violet', 'moonlight', 'red', 'blue', 'lime', 'soft_white', 'daylight', 'warm_white', 'orange',
              'yellow', 'green', 'coral', 'cold_white', 'raspberry', 'turquoise', 'cyan', 'purple', 'orchid']

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logger = logging.Logger('api_logs', logging.INFO)
MY_HOST = "localhost:1488"


class DeviceInfo:
    def __init__(self, device_id, name, state, properties, item_type):
        self.id = device_id
        self.name = name
        self.state = state
        self.properties = properties
        self.item_type = item_type

    def __repr__(self):
        return "".join(f"{self.__dict__.values()}")


class Iot:
    @staticmethod
    def set_on_off(state: bool):
        return json.dumps(
            {"actions": [{"type": "devices.capabilities.on_off", "state": {"instance": "on", "value": state}}]})

    @staticmethod
    def change_brightness(value):
        if 0 <= value <= 100:
            return json.dumps(
                {"actions": [
                    {"type": "devices.capabilities.range", "state": {"instance": "brightness", "value": value}}]})
        raise ValueError("value must be <= 100 an >= 1")

    @staticmethod
    def change_color(color):
        # if color in COLOR_LIST:
        return json.dumps(
            {"actions": [
                {"type": "devices.capabilities.color_setting", "state": {"instance": "color", "value": color}}]})

        # raise ValueError("value must be in color list")

    @staticmethod
    def state():
        url = 'https://iot.quasar.yandex.ru/m/user/devices?sync_provider_states=1'
        r = requests.get(url, headers=HEADERS)
        # print(r.text)
        data = json.loads(r.text)
        with open("test.json", "w", encoding="utf-8") as f:
            f.write(r.text)
        devices = data.get('rooms')[0].get('devices')
        groups = data.get("groups")
        # print(devices)
        res = {}
        for group in groups:
            try:
                res[group.get('id')] = group.get('capabilities')[0].get('state').get('value')
            except AttributeError:
                res[group.get('id')] = False
        for device in devices:
            try:
                res[device.get('id')] = device.get('capabilities')[0].get('state').get('value')
            except AttributeError:
                res[device.get('id')] = False

        return res

    @staticmethod
    def state_v3():
        url = "https://iot.quasar.yandex.ru/m/v3/user/devices"
        r = requests.get(url, headers=HEADERS)
        print(r.text)
        data = json.loads(r.text)
        devices = data.get("households")[0].get("all")
        res = []
        for device in devices:
            device_id = device.get("id")
            name = device.get("name")
            state = device.get("capabilities")[0].get("state")
            if not state:
                state = False
            else:
                state = state.get("value")
            properties = device.get("properties")
            item_type = device.get("item_type")
            res.append(
                DeviceInfo(device_id, name, state, properties, item_type)
            )
        return res

    @staticmethod
    def get_csrf():
        r = requests.get('https://yandex.ru/quasar/iot', headers=HEADERS)
        l = len('window.storage={"csrfToken2":"')
        start = r.text.find('window.storage={"csrfToken2":"') + l
        end = r.text.find('"', start)
        return r.text[start:end]

    @staticmethod
    def update_csrf():
        print('updating csrf')
        with open('headers.json', 'w') as f:
            HEADERS['x-csrf-token'] = Iot.get_csrf()
            json.dump(HEADERS, f)


class Device:
    def __init__(self, info: DeviceInfo):
        self.id = info.id
        self.name = info.name
        self.device_url = f'https://iot.quasar.yandex.ru/m/user/devices/{self.id}/actions'
        self.state = info.state
        self.type = info.item_type
        self.properties = info.properties
        self.updates_url = None

    def __repr__(self):
        return f"{self.name} with id:{self.id}, state:{self.state}, props:{self.properties}"

    def request(self, data):
        r = requests.post(self.device_url, data=data, headers=HEADERS)
        if r.status_code == 403:
            Iot.update_csrf()
            r2 = requests.post(self.device_url, data=data, headers=HEADERS)
            if r2.status_code != 200:
                raise requests.exceptions.HTTPError(f"{r.status_code}; {r.text}")
        elif r.status_code == 200:
            pass
        else:
            print(f'{r.status_code}; error')
            raise requests.exceptions.HTTPError(f"{r.status_code}; {r.text}")
        return True

    def get_updates_url(self):
        state_url = f'https://iot.quasar.yandex.ru/m/user/devices/{self.id}'
        r = requests.get(state_url, headers=HEADERS)
        data = json.loads(r.text)
        self.state = bool(data.get('capabilities')[0].get('state').get('value'))
        self.updates_url = data.get("updates_url")

    def get_state(self):
        return {
            "state": self.state
        }


class MyNodejsXiaomiDevice:
    def __init__(self, device_id, name):
        self.device_id = device_id
        self.name = name

    def request(self, path, **kwargs):
        url = f"http://{MY_HOST}/{path}"
        kwargs["device"] = self.device_id
        r = requests.get(url, params=kwargs)
        if r.status_code == 200:
            return r.text
        else:
            raise requests.exceptions.HTTPError(f"{r.status_code}; {r.text}")

    def turn_on(self):
        return self.request('turn_on')

    def turn_off(self):
        return self.request('turn_off')


class Scenario(Device):
    def __init__(self, device_id, children=None):
        super().__init__(device_id)
        self.children = children
        print(self.children)
        self.device_url = f'https://iot.quasar.yandex.ru/m/user/scenarios/{self.id}/actions'
        self.type = "scenario"

    def execute(self):
        if self.children:
            for child in self.children:
                child.state = False
        return self.request({})


class Switch(Device):
    def __init__(self, info: DeviceInfo):
        super().__init__(info)
        logger.info(f'starting {self.id} from state {self.state}')
        self.type = "switch"

    def change_state(self, state):
        self.state = state
        return self.request(Iot.set_on_off(state))

    def turn_on(self):
        return self.change_state(True)

    def turn_off(self):
        return self.change_state(False)

    def blink(self, check_state=True):
        if check_state:
            self.state = Iot.state().get(self.id)
        thread = threading.Thread(target=self._blink)
        thread.start()
        return True

    def _blink(self):
        self.change_state(not self.state)
        time.sleep(1)
        return self.change_state(not self.state)

    def get_state(self):
        return {
            "state": self.state
        }


class Humidifier(Switch):
    def __init__(self, info: DeviceInfo):
        super().__init__(info)
        try:
            self.humidity = info.properties[0].get("state").get("value")
            self.temperature = info.properties[1].get("state").get("value")
        except AttributeError:
            self.humidity = 50
            self.temperature = 20
        self.type = "humidifier"

    def update_state(self):
        state_url = f'https://iot.quasar.yandex.ru/m/user/devices/{self.id}'
        r = requests.get(state_url, headers=HEADERS)
        data = json.loads(r.text)
        try:
            self.humidity = data.get('properties')[0].get('state').get('value')
            self.temperature = data.get('properties')[1].get('state').get('value')
            self.state = data.get('capabilities')[0].get('state').get('value')
        except AttributeError:
            self.humidity = 50
            self.temperature = 20
            self.state = False

    def get_state(self):
        return {
            "state": self.state,
            "temperature": self.temperature,
            "humidity": self.humidity
        }


class Light(Switch):
    def __init__(self, info: DeviceInfo):
        super().__init__(info)
        self.brightness = 50
        self.palette = []
        self.color = 'soft_white'
        self.type = "light"

    def change_color(self, color):
        self.color = color
        return self.request(Iot.change_color(color))

    def change_brightness(self, value):
        if not self.state:
            self.turn_on()
        self.brightness = value
        return self.request(Iot.change_brightness(value))

    def get_state(self):
        state_url = f'https://iot.quasar.yandex.ru/m/user/devices/{self.id}'
        r = requests.get(state_url, headers=HEADERS)
        data = json.loads(r.text)
        self.palette = data.get('capabilities')[1].get('parameters').get('palette')
        c = data.get('capabilities')[1].get('state').get('value')
        self.state = bool(data.get('capabilities')[0].get('state').get('value'))
        self.color = c.get('id')
        if not self.color or self.color == "":
            def _calc(color_val):
                return color_val.get('h') ** 2 + color_val.get('s') ** 2 + color_val.get('v') ** 2

            m = 10000000, None
            color_sum = _calc(c.get('value'))
            for color in self.palette:
                a = _calc(color.get('value'))
                if abs(a - color_sum) < m[0]:
                    m = abs(a - color_sum), color.get('id')
            self.color = m[1]
        self.brightness = data.get('capabilities')[2].get('state').get('value')

        return {
            "state": self.state,
            "color": self.color,
            "brightness": self.brightness,
            "palette": self.palette
        }

    def blink_color(self, colors, interval=1, check_state=True):
        if check_state:
            self.get_state()

        if not self.state:
            self._blink()
        else:
            def _():
                for color in colors:
                    self.change_color(color)
                self.change_color(self.color)

            _()
        return True

    def blink_brightness(self, values, interval=1, check_state=True):
        if check_state:
            self.get_state()

        def _():
            for value in values:
                self.change_brightness(value)
            self.change_brightness(self.brightness)

        _()
        return True


class AdvancedLight(Light):
    def __init__(self, info: DeviceInfo, ip, token):
        self._device = Yeelight(ip, token)
        super().__init__(info)
        self.color_temp = 0
        self.mode = 0
        self.rgb = 0
        self.get_state()

    def get_brightness(self):
        if self.mode != 5:
            return self.brightness
        return 1

    def blink(self, check_state=True):
        if not self._device:
            super().blink(check_state)
        else:
            def _blink():
                self._device.toggle()
                time.sleep(1)
                self._device.toggle()

            threading.Thread(target=_blink).start()

    def change_state(self, state):
        self.state = state
        if state:
            return self._device.on()
        else:
            return self._device.off()

    def turn_on(self):
        self.state = True
        return self._device.on()

    def change_mode(self, mode):
        self.mode = mode
        return self._device.on(mode=mode)

    def set_rbg(self, rgb):
        self.rgb = rgb
        return self._device.set_rgb(rgb)

    def turn_off(self):
        self.state = False
        return self._device.off()

    def change_brightness(self, value):
        if value <= 1:
            self._device.set_brightness(1)
            self.brightness = 1
            self._device.on(mode=5)
            self.mode = 5
            return
        elif value > 1 and self.mode == 5:
            self._device.on(mode=1)
            self.mode = 1
        elif not self.state:
            self._device.on()

        self.brightness = value
        return self._device.set_brightness(value)

    def get_state(self):
        status = self._device.status()
        if status.moonlight_mode:
            mode = 5
        elif status.color_flowing:
            mode = 4
        else:
            mode = status.color_mode

        self.state = status.is_on
        self.rgb = status.rgb
        self.mode = mode
        self.brightness = status.brightness
        self.color_temp = status.color_temp

        return {
            "state": self.state,
            "rgb": self.rgb,
            "mode": self.mode,
            "brightness": self.brightness,
            "temp": self.color_temp,
        }

    def update_state(self):
        self.state = self._device.status().is_on


class AirBlower(MyNodejsXiaomiDevice):
    def __init__(self, device_id, name=None):
        super(AirBlower, self).__init__(device_id, name)
        if not name:
            self.name = device_id
        self.power = None
        self.fan_level = None
        self.heater = None
        self.alarm = None
        self.temperature = None
        self.update_state()

    def request(self, path, **kwargs):
        if path == 'turn_on_heat':
            self.heater = True
        elif path == 'turn_off_heat':
            self.heater = False
        elif path == 'turn_on_sound':
            self.alarm = True
        elif path == 'turn_off_sound':
            self.alarm = False
        return super().request(path, **kwargs)

    def update_state(self):
        state = json.loads(self.request("status"))

        for attr in state:
            if attr.get("name") == "power":
                self.power = attr.get("value")
            elif attr.get("name") == "fan_level":
                self.fan_level = attr.get("value")
            elif attr.get("name") == "heater":
                self.heater = attr.get("value")
            elif attr.get("name") == "alarm":
                self.alarm = attr.get("value")
            elif attr.get("name") == "temperature":
                self.temperature = attr.get("value")

    def set_fan_level(self, speed):
        if not self.power:
            self.turn_on()
        self.fan_level = speed
        return self.request('set_fan_level', speed=speed)


class AbstractServer:
    def __init__(self, id, name, host):
        self.id = id
        self.name = name
        self.host = host
        self.internet = {"download": 0, "upload": 0, "ping": 0}
        try:
            self.sensors = []
            self.cpu = {}
            self.memory = {}
        except AttributeError:
            pass

    # noinspection DuplicatedCode,PyUnresolvedReferences
    def get_internet_speed(self):
        st = speedtest.Speedtest()
        st.get_best_server([])
        d = st.download()
        download_speed = d / 1024 / 1024
        print("download completed")
        upload_speed = st.upload() / 1024 / 1024
        print("upload completed")
        ping = min(st.get_servers([]).keys())
        print("test completed")
        self.internet = {"download": download_speed, "upload": upload_speed, "ping": ping}
        return self.internet

    def get_sensors_info(self):
        raise NotImplementedError()

    @property
    def temperature(self):
        raise NotImplementedError()

    def get_state(self):
        raise NotImplementedError()


class Raspberry(AbstractServer):
    def get_state(self):
        pass

    def get_sensors_info(self):
        pass

    def __init__(self, id, name):
        super().__init__(id, name, "localhost")
        self.cpu_temp = CPUTemperature()

    @property
    def sensors(self):
        return [{
            "name": "CPU Temperature",
            "value": self.temperature,
            "comparative": "75",
            "unit": "°C",
            "comparativeName": "high",
            "hasComparative": True
        }]

    @property
    def temperature(self):
        return self.cpu_temp.temperature

    @property
    def cpu(self):
        cpu_freq = psutil.cpu_freq()
        return {"percent": psutil.cpu_percent(0.7),
                "freq": {"value": int(cpu_freq.current), "min": int(cpu_freq.min), "max": int(cpu_freq.max)}
                }

    @property
    def memory(self):
        _memory = psutil.virtual_memory()
        return {
            "percent": _memory.percent,
            "total": _memory.total / 1024 / 1024 / 1024,
            "used": _memory.used / 1024 / 1024 / 1024,
        }

    def __repr__(self):
        return f"{self.name}; t: {self.temperature}"


class Server(AbstractServer):
    def __init__(self, id, name, host):
        super().__init__(id, name, host)
        self._temperature = -1
        self.sensors = []

    def get_sensors_info(self):
        return requests.get(f"http://{self.host}/sensors")

    @property
    def temperature(self):
        return self._temperature

    def get_state(self):
        r = json.loads(requests.get(f"http://{self.host}/sensors").text)
        self.sensors = r.get("sensors")
        print(self.sensors)
        self.cpu = r.get("cpu")
        self.memory = r.get("memory")
        self._temperature = r.get("temperature") if r.get("temperature") is not None else -1
        return self.sensors
