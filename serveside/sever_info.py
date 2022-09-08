import psutil
import speedtest


def get_temperature():
    t = list(filter(lambda el: el.label == "CPU Temperature", psutil.sensors_temperatures().get("atk0110")))[0].current
    return t


def get_internet_speed():
    st = speedtest.Speedtest()
    st.get_best_server([])
    d = st.download()
    download_speed = d / 1024 / 1024
    print("download completed")
    upload_speed = st.upload() / 1024 / 1024
    print("upload completed")
    ping = min(st.get_servers([]).keys())
    print("test completed")
    return download_speed, upload_speed, ping


def get_sensors():
    sensors = []
    for i in psutil.sensors_temperatures().values():
        for j in i:
            if j.label == "":
                j = list(j)
                j[0] = "PCI Adapter"
            sensors.append({
                "name": j[0],
                "value": j[1],
                "hasComparative": True,
                "comparative": j[2],
                "comparativeName": "high",
                "unit": "°C"
            })

    for i in psutil.sensors_fans().values():
        for j in i:
            sensors.append({
                "name": j[0].replace(" Speed", ""),
                "value": j[1],
                "unit": "RPM",
                "has_comparative": False,
                "format": "%.0f"
            })
    cpu_freq = psutil.cpu_freq()
    cpu = {"percent": psutil.cpu_percent(0.7),
           "freq": {"value": int(cpu_freq.current * 1000), "min": int(cpu_freq.min), "max": int(cpu_freq.max)}
           }

    _memory = psutil.virtual_memory()
    memory = {
        "percent": _memory.percent,
        "total": _memory.total / 1024 / 1024 / 1024,
        "used": _memory.used / 1024 / 1024 / 1024,
    }

    _temperature = int(
        list(filter(lambda x: x.get("name") == "CPU Temperature", sensors))[0].get("value"))
    return {"sensors": sensors, "cpu": cpu, "memory": memory, "temperature": _temperature}
