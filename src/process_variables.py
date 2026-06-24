import xarray as xr
import pandas as pd


def temperatura_celsius(file):
    file_celsius = file.copy()
    if "utci" in file_celsius:
        file_celsius["utci_celsius"] = file_celsius["utci"] - 273.15
        file_celsius["utci_celsius"].attrs["units"] = "degC"
        file_celsius["utci_celsius"].attrs["long_name"] = (
            "Universal Thermal Climate Index in Celsius"
        )
    return file_celsius


def ajustar_zona_horaria_mexico(file):
    file_mexico = file.copy()
    seis_horas_atras = pd.to_timedelta(6, unit="h")
    file_mexico["time"] = file_mexico["time"] - seis_horas_atras
    return file_mexico
