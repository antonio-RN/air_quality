from prefect import flow
from prefect_dask import DaskTaskRunner

from conf import parameters
from src.nodes import (
    create_geodataframe,
    input_missing_data,
    input_raw_data,
    pivoting_raw_data,
    reduce_raw,
    save_geodataframe,
    transform_datetime,
)


@flow(
    name="Data processing",
    version="0.1",
    task_runner=DaskTaskRunner(),
    log_prints=True,
)
def data_pipeline():
    dd_raw = input_raw_data(parameters.raw_file, parameters.csv_blocksize)
    dd_raw_reduced = reduce_raw(dd_raw, parameters.n_partitions)
    dd_pivoted = dd_raw_reduced.map_partitions(
        pivoting_raw_data, meta=parameters.meta_pivoted
    )
    dd_datetime = dd_pivoted.map_partitions(
        transform_datetime, meta=parameters.meta_datetime
    )
    dd_bronze = dd_datetime.map_partitions(
        input_missing_data, meta=parameters.meta_bronze
    )
    dd_bronze = dd_bronze.repartition(npartitions=dd_bronze.npartitions)
    dd_bronze.to_parquet(parameters.bronze_file)
    gdd_bronze = create_geodataframe(dd_bronze)
    save_geodataframe(
        gdd_bronze, parameters.n_partitions_geo, parameters.bronze_geofile
    )
