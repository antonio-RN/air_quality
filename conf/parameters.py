from pathlib import Path

# data sources and paths

data_folder = Path.cwd().joinpath("data")
raw_file = data_folder.joinpath("01_raw").joinpath("airquality_raw_20250514.csv")
bronze_file = data_folder.joinpath("02_intermediate").joinpath("dd_log_bronze.parquet")
bronze_geofile = data_folder.joinpath("02_intermediate").joinpath("gdd_log_bronze.parquet")

# load and save params

csv_blocksize = "10MB"
n_partitions = 2

