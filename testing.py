"""
Standalone script for iterative development without Prefect orchestration.

Usage:
    uv run python testing.py

This mirrors the Prefect pipeline logic but executes eagerly,
making it faster for debugging and iteration.
"""

from conf import parameters
from src import nodes


def main():
    dd_raw = nodes.input_raw_data(parameters.raw_file, parameters.csv_blocksize)
    dd_raw_reduced = nodes.reduce_raw(dd_raw, parameters.n_partitions)

    dd_pivoted = dd_raw_reduced.map_partitions(
        nodes.pivoting_raw_data, meta=parameters.meta_pivoted
    )

    dd_datetime = dd_pivoted.map_partitions(
        nodes.transform_datetime, meta=parameters.meta_datetime
    )

    dd_bronze = dd_datetime.map_partitions(
        nodes.input_missing_data, meta=parameters.meta_bronze
    )

    dd_bronze.to_parquet(parameters.bronze_file)
    print(f"Bronze data saved to {parameters.bronze_file}")

    gdd_bronze = nodes.create_geodataframe(dd_bronze)
    nodes.save_geodataframe(
        gdd_bronze, parameters.n_partitions_geo, parameters.bronze_geofile
    )
    print(f"Geo bronze data saved to {parameters.bronze_geofile}")


if __name__ == "__main__":
    main()
