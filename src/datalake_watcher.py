import os
import time
import xarray as xr
import pandas as pd
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCH_DIRECTORY = os.path.abspath(os.path.join(BASE_DIR, "../datalake/002_trusted"))
OUTPUT_DIRECTORY = os.path.abspath(os.path.join(BASE_DIR, "../datalake/003_processed"))

os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)


def convert_kelvin_to_celsius(dataset: xr.Dataset, variable: str = "utci") -> xr.Dataset:
    if variable in dataset:
        dataset[variable] = dataset[variable] - 273.15
        dataset[variable].attrs['units'] = 'Celsius'
    return dataset


def add_dynamic_local_time_variable(dataset: xr.Dataset, time_dimension: str = 'time') -> xr.Dataset:
    utc_times = pd.DatetimeIndex(dataset[time_dimension].values)
    if utc_times.tz is None:
        utc_times = utc_times.tz_localize('UTC')
        
    lons = dataset['lon'].values
    lats = dataset['lat'].values
    times = dataset[time_dimension].values
    
    local_time_matrix = np.zeros((len(times), len(lats), len(lons)), dtype='datetime64[ns]')
    
    for lon_idx, lon in enumerate(lons):
        if lon <= -114.75:
            tz = 'America/Tijuana'
        elif -114.75 < lon <= -104.5:
            tz = 'America/Mazatlan'
        elif lon >= -88.5:
            tz = 'America/Cancun'
        else:
            tz = 'America/Mexico_City'
            
        local_tz_times = utc_times.tz_convert(tz).tz_localize(None).values
        local_time_matrix[:, :, lon_idx] = local_tz_times[:, np.newaxis]
        
    dataset['local_time'] = (('time', 'lat', 'lon'), local_time_matrix)
    dataset['local_time'].attrs['description'] = 'Local time calculated dynamically based on longitude'
    return dataset


def wait_for_file_release(file_path: str, timeout: int = 60) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with open(file_path, 'rb'):
                return True
        except IOError:
            time.sleep(2)
    return False


def process_file(file_path: str):
    try:
        if not wait_for_file_release(file_path):
            print(f"[ERROR] Timeout waiting for file release: {file_path}")
            return

        print(f"processing for: {file_path}")
        
        ds = xr.open_dataset(file_path)
        ds = convert_kelvin_to_celsius(ds, variable="utci")
        ds = add_dynamic_local_time_variable(ds, time_dimension="time")
        
        filename = os.path.basename(file_path)
        output_path = os.path.join(OUTPUT_DIRECTORY, f"processed_{filename}")
        
        ds.to_netcdf(output_path)
        print(f"[SUCCESS] Saved processed NetCDF file to: {output_path}")
        
        ds.close()

    except Exception as e:
        print(f"[ERROR] Failed to process {file_path}: {e}")


class DataLakeHandler(FileSystemEventHandler):
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        if event.src_path.endswith('.nc') or event.src_path.endswith('.nc4'):
            time.sleep(10) 
            process_file(event.src_path)


if __name__ == "__main__":
    event_handler = DataLakeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_DIRECTORY, recursive=False)
    
    print(f"[START] Monitoring directory: '{WATCH_DIRECTORY}'")
    print(f"[START] Target output directory: '{OUTPUT_DIRECTORY}'")
    observer.start()
    
    try:
        observer.join()
    except KeyboardInterrupt:
        print(f"\n[STOP] Stopping observer...")
        observer.stop()
        observer.join()
