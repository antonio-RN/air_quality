from pathlib import Path

import dask.dataframe as dd
import dask_geopandas
import geopandas as gpd
import numpy as np
import pandas as pd
from prefect import task


@task(
    retries=3,
    retry_delay_seconds=30,
    timeout_seconds=600,
)
def input_raw_data(param_raw_file: Path, param_csv_blocksize: str) -> dd.DataFrame:
    dd_raw = dd.read_csv(
        param_raw_file,
        blocksize=param_csv_blocksize,
        dtype={"Georeferència": "str"},
        engine="pyarrow",
    )
    return dd_raw


@task(retries=2, retry_delay_seconds=5, timeout_seconds=120)
def reduce_raw(df_raw: dd.DataFrame, param_n_partitions: int) -> dd.DataFrame:
    df_raw_reduced = df_raw.partitions[0:param_n_partitions]
    return df_raw_reduced


@task(retries=2, retry_delay_seconds=10, timeout_seconds=600)
def pivoting_raw_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    df_pivoted = df_raw.drop(columns=["Georeferència"]).melt(
        id_vars=[
            "CODI EOI",
            "NOM ESTACIO",
            "DATA",
            "MAGNITUD",
            "CONTAMINANT",
            "UNITATS",
            "TIPUS ESTACIO",
            "AREA URBANA",
            "CODI INE",
            "MUNICIPI",
            "CODI COMARCA",
            "NOM COMARCA",
            "ALTITUD",
            "LATITUD",
            "LONGITUD",
        ],
        value_vars=[
            "01h",
            "02h",
            "03h",
            "04h",
            "05h",
            "06h",
            "07h",
            "08h",
            "09h",
            "10h",
            "11h",
            "12h",
            "13h",
            "14h",
            "15h",
            "16h",
            "17h",
            "18h",
            "19h",
            "20h",
            "21h",
            "22h",
            "23h",
            "24h",
        ],
        var_name="HORA",
        value_name="VALOR",
    )
    return df_pivoted


@task(retries=2, retry_delay_seconds=10, timeout_seconds=600)
def transform_datetime(df_pivoted: pd.DataFrame) -> pd.DataFrame:
    is_24h = df_pivoted["HORA"] == "24h"
    df_pivoted = df_pivoted.assign(
        HORA_tmp=df_pivoted.loc[:, "HORA"].str[:-1].replace("24", "00").astype(int)
    )
    df_datetime = df_pivoted.assign(
        DATA_HORA=pd.to_datetime(
            df_pivoted.loc[:, "DATA"].astype(str)
            + " "
            + df_pivoted.loc[:, "HORA_tmp"].astype(str),
            format="%d/%m/%Y %H",
        )
    ).drop(columns=["DATA", "HORA", "HORA_tmp"])
    df_datetime.loc[is_24h, "DATA_HORA"] += pd.Timedelta(days=1)
    return df_datetime


@task(retries=2, retry_delay_seconds=10, timeout_seconds=600)
def input_missing_data(df_pivoted: pd.DataFrame) -> pd.DataFrame:
    df_pivoted = df_pivoted.dropna(subset=["VALOR"]).reset_index(drop=False)
    for col in ["ALTITUD", "LATITUD", "LONGITUD"]:
        n_zeros = (df_pivoted[col] == 0).sum()
        if n_zeros > 0:
            df_pivoted[col] = df_pivoted[col].replace(0, np.nan)

    missing_station = df_pivoted.query("`NOM ESTACIO`.isna()")
    df_pivoted_info = missing_station.loc[
        :, ["index", "CODI EOI", "MAGNITUD", "DATA_HORA"]
    ]
    df_missing_eoi_list = missing_station.loc[:, "CODI EOI"].unique()

    df_correct_info = (
        df_pivoted.dropna(subset=["NOM ESTACIO"])
        .query(
            "`CODI EOI` in (@df_missing_eoi_list)",
            local_dict={"df_missing_eoi_list": df_missing_eoi_list},
        )
        .drop(
            columns=[
                "index",
                "VALOR",
                "CODI INE",
                "CODI COMARCA",
                "NOM COMARCA",
                "DATA_HORA",
            ]
        )
        .groupby(["CODI EOI", "MAGNITUD"])
        .head(1)
    )

    df_merged = (
        df_pivoted_info.merge(
            df_correct_info,
            on=["CODI EOI", "MAGNITUD"],
            how="left",
            suffixes=["_x", ""],
        )
        .drop(columns=["MAGNITUD", "DATA_HORA"])
        .set_index("index")
    )
    df_bronze = (
        df_pivoted.set_index("index").combine_first(df_merged).reset_index(drop=True)
    )

    return df_bronze.loc[
        :,
        [
            "CODI EOI",
            "NOM ESTACIO",
            "MAGNITUD",
            "CONTAMINANT",
            "UNITATS",
            "TIPUS ESTACIO",
            "AREA URBANA",
            "CODI INE",
            "MUNICIPI",
            "CODI COMARCA",
            "NOM COMARCA",
            "ALTITUD",
            "LATITUD",
            "LONGITUD",
            "VALOR",
            "DATA_HORA",
        ],
    ]


@task(retries=2, retry_delay_seconds=10, timeout_seconds=600)
def create_geodataframe(df_bronze: pd.DataFrame) -> gpd.GeoDataFrame:
    temp_geometry = dask_geopandas.points_from_xy(
        df=df_bronze,
        x="LONGITUD",
        y="LATITUD",
    )
    df_bronze = df_bronze.assign(geometry=temp_geometry)
    gdf_bronze = (
        dask_geopandas.from_dask_dataframe(df_bronze)
        .drop(columns=["LATITUD", "LONGITUD"])
        .set_crs("EPSG:4326")
    )
    return gdf_bronze


@task(
    retries=3,
    retry_delay_seconds=30,
    timeout_seconds=600,
)
def save_geodataframe(
    gdf_bronze: dask_geopandas.GeoDataFrame,
    param_n_partitions_geo: int,
    param_bronze_geofile: Path,
) -> None:
    temp_gdf_bronze = gdf_bronze.repartition(npartitions=param_n_partitions_geo)
    temp_gdf_bronze.to_parquet(param_bronze_geofile)
    return None
