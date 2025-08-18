from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ISOSIMpy")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"
