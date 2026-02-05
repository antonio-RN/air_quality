"""
This is a boilerplate pipeline 'pipe_guided_exploration'
generated using Kedro 1.0.0
"""
import pandas as pd
from datetime import datetime, timedelta
import dask.dataframe as dd
import dask_geopandas
import geopandas as gpd


def convert_to_dask(df_raw: pd.DataFrame, max_rows_chunk: int) -> dd:
    dd_raw = dd.from_pandas(df_raw, chunksize=max_rows_chunk)
    return dd_raw

def reduce_raw(dd_raw: dd, max_raw_rows: int) -> dd:
    dd_raw_reduced = df_raw.get_partition(0)
    return dd_raw_reduced


def pivoting_raw_data(df_raw: dd) -> dd:
    df_pivoted = (
        df_raw
        .drop(columns=["Georeferència"])
        .melt(id_vars=[
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
    )
    return df_pivoted


def transform_datetime(df_pivoted: pd.DataFrame) -> pd.DataFrame:
    df_pivoted.loc[:, "HORA"] = (
        df_pivoted.loc[:, "HORA"].str.replace("h", "").astype(int) - 1
    )
    df_pivoted_datetime = df_pivoted.assign(
        DATA_HORA=lambda s: s.apply(
            lambda row: datetime.strptime(
                row.loc["DATA"] + " " + str(row.loc["HORA"]) + ":00", "%d/%m/%Y %H:%M"
            )
            + timedelta(hours=1),
            axis=1,
        )
    ).drop(columns=["DATA", "HORA"])
    return df_pivoted_datetime


def input_missing_data(df_pivoted_datetime: pd.DataFrame) -> pd.DataFrame:
    df_pivoted_datetime = df_pivoted_datetime.dropna(subset=["VALOR"]).reset_index(
        drop=False
    )  # drop missing measurements
    df_pivoted_datetime.replace(
        {"ALTITUD": {0: pd.NA}, "LATITUD": {0: pd.NA}, "LONGITUD": {0: pd.NA}},
        inplace=True,
    )  # clear wrong geopositional data (0 -> NaN)
    df_pivoted_datetime_info = df_pivoted_datetime.query("`NOM ESTACIO`.isna()").loc[
        :, ["index", "CODI EOI", "MAGNITUD", "DATA_HORA"]
    ]
    df_missing_eoi_list = (
        df_pivoted_datetime.query("`NOM ESTACIO`.isna()").loc[:, "CODI EOI"].unique()
    )
    df_correct_info = (
        df_pivoted_datetime.dropna(subset=["NOM ESTACIO"])
        .query("`CODI EOI` in (@df_missing_eoi_list)")
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
        pd.merge(
            df_pivoted_datetime_info,
            df_correct_info,
            on=["CODI EOI", "MAGNITUD"],
            how="left",
            suffixes=["_x", ""],
        )
        .drop(columns=["CODI EOI", "MAGNITUD", "DATA_HORA"])
        .set_index("index")
    )
    df_bronze = df_pivoted_datetime.set_index("index").combine_first(
        df_merged
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


def create_geodataframe(df_bronze: pd.DataFrame) -> gpd.GeoDataFrame:
    gdf_bronze = gpd.GeoDataFrame(
        df_bronze,
        geometry=gpd.points_from_xy(
            df_bronze.loc[:, "LONGITUD"], df_bronze.loc[:, "LATITUD"], crs="EPSG:4326"
        ),
    ).drop(columns=["LATITUD", "LONGITUD"])
    return gdf_bronze
