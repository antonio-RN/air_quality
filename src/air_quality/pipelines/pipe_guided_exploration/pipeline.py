"""
This is a boilerplate pipeline 'pipe_guided_exploration'
generated using Kedro 1.0.0
"""

from kedro.pipeline import Node, Pipeline  # noqa
from .nodes import (
    convert_to_dask,
    reduce_raw,
    pivoting_raw_data,
    transform_datetime,
    input_missing_data,
    create_geodataframe,
)


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            Node(
                func=convert_to_dask,
                inputs=["air_quality_log", "params:max_rows_chunk"],
                outputs="dd_log_raw",
            ),
            Node(
                func=reduce_raw,
                inputs=["dd_log_raw", "params:max_raw_rows"],
                outputs="dd_log_raw_r",
            ),
            Node(
                func=pivoting_raw_data,
                inputs="dd_log_raw_r",  # change to "air_quality_log_r" if the previous node is not commented out
                outputs="dd_log_pivoted",
            ),
            Node(
                func=transform_datetime,
                inputs="dd_log_pivoted",
                outputs="dd_log_datetime",
            ),
            Node(
                func=input_missing_data,
                inputs="dd_log_datetime",
                outputs="dd_log_clean",
            ),
            Node(
                func=create_geodataframe,
                inputs="dd_log_clean",
                outputs="gdd_log_bronze",
            ),
        ]
    )
