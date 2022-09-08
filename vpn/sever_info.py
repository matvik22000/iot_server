import psutil


def get_sensors():
    sensors = []
    cpu_freq = psutil.cpu_freq()
    cpu = {"percent": psutil.cpu_percent(0.7),
           "freq": {"value": int(cpu_freq.current), "min": int(cpu_freq.min), "max": int(cpu_freq.max)}
           }

    _memory = psutil.virtual_memory()
    memory = {
        "percent": _memory.percent,
        "total": _memory.total / 1024 / 1024 / 1024,
        "used": _memory.used / 1024 / 1024 / 1024,
    }

    return {"sensors": sensors, "cpu": cpu, "memory": memory}


