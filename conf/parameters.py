from pathlib import Path

# data sources and paths

data_folder = Path.cwd().parent.joinpath("data")
raw_file = data_folder.joinpath("01_raw").joinpath("airquality_raw_20250514.csv")

# load and save params

max_raw_rows = 100000
n_partitions = 2
csv_blocksize = "200MB"
