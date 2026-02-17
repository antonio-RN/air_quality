from conf import parameters
from src import nodes  # , pipeline
import dask.dataframe as dd

dd_raw = nodes.input_raw_data(parameters.raw_file, parameters.csv_blocksize)
dd_raw_reduced = nodes.reduce_raw(dd_raw, parameters.n_partitions)
dd_pivoted = dd_raw_reduced.map_partitions(
    nodes.pivoting_raw_data, meta=nodes.pivoting_raw_data(dd_raw_reduced.head(1))
)
dd_datetime = dd_pivoted.map_partitions(
    nodes.transform_datetime, meta=nodes.transform_datetime(dd_pivoted.head(1))
)
dd_bronze = dd_datetime.map_partitions(nodes.input_missing_data)
dd_bronze.to_parquet(parameters.bronze_file)
del dd_raw, dd_raw_reduced, dd_pivoted, dd_datetime

del dd_bronze
dd_bronze = dd.read_parquet(parameters.bronze_file)
gdd_bronze = dd_bronze.map_partitions(nodes.create_geodataframe)
del dd_bronze
nodes.save_geodataframe(
    gdd_bronze, parameters.n_partitions_geo, parameters.bronze_geofile
)
