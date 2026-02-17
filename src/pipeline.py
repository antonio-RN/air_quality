from prefect import flow
from src.nodes import (
    input_raw_data,
    reduce_raw,
    pivoting_raw_data,
    transform_datetime,
    input_missing_data,
    create_geodataframe,
    save_geodataframe,
)
from conf import parameters

import dask.dataframe as dd


@flow(name="Data processing", version="0.1")
def data_pipeline():
    dd_raw = input_raw_data(parameters.raw_file, parameters.csv_blocksize)
    dd_raw_reduced = reduce_raw(dd_raw, parameters.n_partitions)
    del dd_raw
    dd_pivoted = dd_raw_reduced.map_partitions(
        pivoting_raw_data, meta=pivoting_raw_data(dd_raw_reduced.head(1))
    )
    del dd_raw_reduced
    dd_datetime = dd_pivoted.map_partitions(
        transform_datetime, meta=transform_datetime(dd_pivoted.head(1))
    )
    del dd_pivoted
    dd_bronze = dd_datetime.map_partitions(input_missing_data)
    dd_bronze.to_parquet(parameters.bronze_file)
    del dd_bronze
    dd_bronze = dd.read_parquet(parameters.bronze_file)
    gdd_bronze = dd_bronze.map_partitions(create_geodataframe)
    del dd_bronze
    # save_geodataframe(
    #     gdd_bronze, parameters.n_partitions_geo, parameters.bronze_geofile
    # )
