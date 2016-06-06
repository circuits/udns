from os import environ


def getenv(*keys, **kwargs):
    for key in keys:
        if key in environ:
            return environ[key]
    if "default" in kwargs:
        return kwargs["default"]
    raise KeyError(key)
