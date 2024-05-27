import os
import time
from time import strftime

base_dir = 'datafolder/'
#spiders = ['cruzverde', 'ahumada', 'salcobrand', 'profar', 'ligafarmacia', 'farmex']  # Asegúrate de que el nombre del spider sea correcto
spiders = ['profar']

if not os.path.exists(base_dir):
    os.makedirs(base_dir)

total_start_time = time.time()

for spider in spiders:
    filename = f'{base_dir}{spider}_{strftime("%Y_%m_%d")}.csv'
    if os.path.exists(filename):
        os.remove(filename)
    command = f'scrapy crawl {spider} -o {filename}'

    start_time = time.time()
    os.system(command)
    elapsed_time = time.time() - start_time
    
    print(f'________________\nFile has been saved:\nDirectory: {filename}')
    print(f'Elapsed time: {elapsed_time:.2f} seconds\n________________')

total_elapsed_time = time.time() - total_start_time
print(f'Total elapsed time for all spiders: {total_elapsed_time:.2f} seconds')
