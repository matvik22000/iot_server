# from miio import ChuangmiPlug
# import app
# token = "7216d1b1f4ae2f9983440f9f1630549a"
# ip = "192.168.86.37"
#
# TOKEN = "c91c49228f9cd2235853a2461575f77a"
# IP = "192.168.86.54"
#
#
# h = ChuangmiPlug(ip=IP, token=TOKEN)
# print(h.status())
#
# # p = ChuangmiPlug(app.SOCKET_IP, app.SOCKET_TOKEN)
# # print(p.off())
# # h = AirHumidifierMiot(app.HUMIDIFIER_IP, app.HUMIDIFIER_TOKEN)
# # print(h.status())
# # print(h.on())
#
#
# # import app, api
# # led = api.Light(app.LED, True)
# # led.get_state()
#
#
# # import speedtest
# # st = speedtest.Speedtest()
# # st.get_best_server([])
# # print(min(st.get_servers([]).keys()))
# # print(st.download())

# import pychromecast
#
# services, browser = pychromecast.discovery.discover_chromecasts()
# print(*[(s.friendly_name, s) for s in services], sep='\n')
import time

import rtmidi
from rtmidi.midiutil import open_midiinput
from rtmidi.midiutil import open_midioutput

midiout = rtmidi.MidiOut()
ports =midiout.get_ports()
# open_midioutput()
midiout.open_port(0)

print(ports)
with midiout:
    note_on = [0x90, 60, 112] # channel 1, middle C, velocity 112
    note_off = [0x80, 60, 0]
    midiout.send_message(note_on)
    time.sleep(0.5)
    midiout.send_message(note_off)
    time.sleep(0.1)


# import psutil
# print(psutil.cpu_percent())
# print(psutil.virtual_memory())
# print(psutil.virtual_memory().total / 1024 / 1024 / 1024)
# print(psutil.virtual_memory().used / 1024 / 1024 / 1024)
# print(2 & 4)



