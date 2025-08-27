"""
This is a boilerplate pipeline 'pipe_guided_exploration'
generated using Kedro 1.0.0
"""

from kedro.pipeline import Node, Pipeline  # noqa
from .nodes import reduce_raw, pivoting_raw_data, transform_datetime, input_missing_data, create_geodataframe

def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline([
        Node(
            func=reduce_raw,
            inputs=["air_quality_log", "params:max_raw_rows"],
            outputs="air_quality_log_r"
        ),
        Node(
            func=pivoting_raw_data,
            inputs="air_quality_log_r",
            outputs="air_quality_transform"
        ),
        Node(
            func=transform_datetime,
            inputs="air_quality_transform",
            outputs="air_quality_transform_2"
        ),
        Node(
            func=input_missing_data,
            inputs="air_quality_transform_2",
            outputs="air_quality_transform_3"
        ),
        Node(
            func=create_geodataframe,
            inputs="air_quality_transform_3",
            outputs="air_quality_bronze"
        )
    ])
