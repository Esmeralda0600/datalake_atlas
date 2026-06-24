import xarray as xr
import pandas as pd

def transformar_a_mexico_celsius(ds):
    """
    Recibe un Dataset de Xarray en Kelvin/UTC y lo 
    devuelve convertido a Celsius y Horario de México (UTC-6).
    """
    # Copiamos para no dañar los datos originales en memoria
    ds_neto = ds.copy()
    
    # 1. Conversión de Kelvin a Celsius
    if 'utci' in ds_neto:
        ds_neto['utci'] = ds_neto['utci'] - 273.15
        ds_neto['utci'].attrs['units'] = 'degC'  # Actualiza la etiqueta
    
    # 2. Ajuste de Zona Horaria (UTC a UTC-6)
    seis_horas_atras = pd.to_timedelta(6, unit='h')
    ds_neto['time'] = ds_neto['time'] - seis_horas_atras
    
    return ds_neto
