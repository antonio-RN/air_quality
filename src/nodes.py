import pandas as pd
import numpy as np
import dask.dataframe as dd
import geopandas as gpd
from pathlib import Path
from prefect import task


@task
def input_raw_data(param_raw_file: Path, param_csv_blocksize: str) -> dd.DataFrame:
    dd_raw = dd.read_csv(
        param_raw_file,
        blocksize=param_csv_blocksize,
        dtype={"Georeferència": "str"},
        engine="pyarrow",
    )
    return dd_raw


@task
def reduce_raw(df_raw: dd.DataFrame, param_n_partitions: int) -> dd.DataFrame:
    df_raw_reduced = df_raw.partitions[0:param_n_partitions]
    return df_raw_reduced


@task
def pivoting_raw_data(df_raw: dd.DataFrame) -> dd.DataFrame:
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


@task
def transform_datetime(df_pivoted: dd.DataFrame) -> dd.DataFrame:
    df_pivoted = df_pivoted.assign(
        HORA_tmp=df_pivoted.loc[:, "HORA"].str[:-1].replace("24", "00").astype(int)
    )
    df_datetime = df_pivoted.assign(
        DATA_HORA=dd.to_datetime(
            df_pivoted.loc[:, "DATA"].astype(str)
            + " "
            + df_pivoted.loc[:, "HORA_tmp"].astype(str),
            format="%d/%m/%Y %H",
        )
    ).drop(columns=["DATA", "HORA", "HORA_tmp"])
    return df_datetime


@task
def input_missing_data(df_pivoted: dd.DataFrame) -> dd.DataFrame:
    df_pivoted = df_pivoted.dropna(subset=["VALOR"]).reset_index(
        drop=False
    )  # drop missing measurements
    df_pivoted = df_pivoted.replace(
        {"ALTITUD": {0: np.nan}, "LATITUD": {0: np.nan}, "LONGITUD": {0: np.nan}},
    )  # clear wrong geopositional data (0 -> NaN)
    df_pivoted_info = df_pivoted.query("`NOM ESTACIO`.isna()").loc[
        :, ["index", "CODI EOI", "MAGNITUD", "DATA_HORA"]
    ]
    df_missing_eoi_list = (
        df_pivoted.query("`NOM ESTACIO`.isna()").loc[:, "CODI EOI"].unique()
    )
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
    )  # create sample dataframe with correct data to input

    df_merged = (
        dd.merge(
            df_pivoted_info,
            df_correct_info,
            on=["CODI EOI", "MAGNITUD"],
            how="left",
            suffixes=["_x", ""],
        )
        .drop(columns=["MAGNITUD", "DATA_HORA"])
        .set_index("index")
    )
    df_bronze = (
        df_pivoted.set_index("index")
        .combine_first(df_merged.compute())
        .reset_index(drop=True)
    )  # merge both keeping the correct info if available

    return df_bronze.loc[
        :,
        [
            "CODI EOI",
            "NOM ESTACIO",
            "CODI INE",
            "MUNICIPI",
            "CODI COMARCA",
            "NOM COMARCA",
            "TIPUS ESTACIO",
            "AREA URBANA",
            "LATITUD",
            "LONGITUD",
            "ALTITUD",
            "MAGNITUD",
            "CONTAMINANT",
            "UNITATS",
            "DATA_HORA",
            "VALOR",
        ],
    ]


@task
def create_geodataframe(df_bronze: dd.DataFrame) -> gpd.GeoDataFrame:
    temp_geometry = gpd.points_from_xy(
        x=df_bronze.loc[:, "LONGITUD"],
        y=df_bronze.loc[:, "LATITUD"],
    )
    gdf_bronze = gpd.GeoDataFrame(
        data=df_bronze.drop(columns=["LONGITUD", "LATITUD"]),
        geometry=temp_geometry,
        crs="EPSG:4326",
    )
    return gdf_bronze


@task
def save_geodataframe(
    gdf_bronze: gpd.GeoDataFrame,
    param_n_partitions_geo: int,
    param_bronze_geofile: Path,
):
    temp_gdf_bronze = gdf_bronze.repartition(npartitions=param_n_partitions_geo)
    temp_gdf_bronze.to_parquet(param_bronze_geofile)
    pass
