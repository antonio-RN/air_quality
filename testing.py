from conf import parameters
from src import nodes # , pipeline

dd_raw = nodes.input_raw_data(parameters.raw_file, parameters.csv_blocksize)
dd_raw_reduced = nodes.reduce_raw(dd_raw, parameters.n_partitions)
dd_pivoted = nodes.pivoting_raw_data(dd_raw_reduced)
dd_datetime = nodes.transform_datetime(dd_pivoted)
dd_bronze = nodes.input_missing_data(dd_datetime)
gdd_bronze = nodes.create_geodataframe(dd_bronze)