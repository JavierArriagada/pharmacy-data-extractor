import os
import time
import logging
import pandas as pd
from datetime import datetime
import subprocess
from tqdm import tqdm

# Variables de configuración
SAVE_LOGS = True
SAVE_ERRORS = True
PROGRESS_INTERVAL = 10  # Intervalo en segundos para mostrar progreso
LOG_DIR = 'logs'  # Directorio para guardar logs
ERROR_LOG_FILE_NAME = 'scrapy_errors.log'
DATE_STR = datetime.now().strftime("%Y-%m-%d")

# Crear directorio de logs si no existe
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configuración del logging
if SAVE_ERRORS:
    logging.basicConfig(
        filename=os.path.join(LOG_DIR, f"{DATE_STR}_{ERROR_LOG_FILE_NAME}"),
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Redirigir logs de Scrapy a nuestro archivo de registro
    from scrapy.utils.log import configure_logging
    configure_logging(install_root_handler=False)
    logging.getLogger('scrapy').addHandler(logging.FileHandler(os.path.join(LOG_DIR, f"{DATE_STR}_{ERROR_LOG_FILE_NAME}")))

base_dir = 'datafolder/'
spiders = ['cruzverde', 'ahumada', 'salcobrand', 'profar', 'ligafarmacia', 'farmex'] 
if not os.path.exists(base_dir):
    os.makedirs(base_dir)

total_start_time = time.time()
spiders_times = []

for spider in tqdm(spiders, desc="Running spiders", mininterval=2):
    command = f'scrapy crawl {spider}'
    spider_log_file = os.path.join(LOG_DIR, f"{DATE_STR}_{spider}_log.log") if SAVE_LOGS else None
    start_time = time.time()
    error_time = None
    try:
        with open(spider_log_file, 'w') if SAVE_LOGS else subprocess.DEVNULL as log_file:
            process = subprocess.Popen(command, shell=True, stdout=log_file, stderr=log_file, text=True)
            while process.poll() is None:
                tqdm.write(f"Spider {spider} is still running...")
                time.sleep(PROGRESS_INTERVAL)
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, command)
    except subprocess.CalledProcessError as e:
        error_time = datetime.now()
        error_message = f"Error running spider {spider} at {error_time}: {e}"
        if SAVE_ERRORS:
            logging.error(error_message)
        elapsed_time = time.time() - start_time
        spiders_times.append({
            'spider': spider,
            'elapsed_time': elapsed_time,
            'error_time': error_time
        })
        continue
    elapsed_time = time.time() - start_time
    spiders_times.append({
        'spider': spider,
        'elapsed_time': elapsed_time,
        'error_time': error_time
    })

total_elapsed_time = time.time() - total_start_time
print(f'Total elapsed time for all spiders: {total_elapsed_time:.2f} seconds')

# Mostrar tabla resumen de tiempos usando pandas
df = pd.DataFrame(spiders_times)
print("\nSummary of individual spider times:")
print(df)

# Guardar el resumen en un archivo CSV
summary_csv_path = os.path.join(LOG_DIR, f"{DATE_STR}_spiders_times_summary.csv")
df.to_csv(summary_csv_path, index=False)
print(f'Summary saved to {summary_csv_path}')

