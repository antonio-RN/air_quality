from pathlib import Path

# data sources and paths

data_folder = Path.cwd().joinpath("data")
raw_file = data_folder.joinpath("01_raw").joinpath("airquality_raw_20250514.csv")
bronze_file = data_folder.joinpath("02_intermediate").joinpath("dd_log_bronze.parquet")
bronze_geofile = data_folder.joinpath("02_intermediate").joinpath(
    "gdd_log_bronze.parquet"
)

# load and save params

csv_blocksize: str = "50MB"
n_partitions: int = 5
n_partitions_geo: int = n_partitions * 5

# Meta schema after pivoting_raw_data (id_vars + HORA + VALOR)
meta_pivoted = {
    "CODI EOI": int,
    "NOM ESTACIO": str,
    "DATA": str,
    "MAGNITUD": int,
    "CONTAMINANT": str,
    "UNITATS": str,
    "TIPUS ESTACIO": str,
    "AREA URBANA": str,
    "CODI INE": int,
    "MUNICIPI": str,
    "CODI COMARCA": int,
    "NOM COMARCA": str,
    "ALTITUD": int,
    "LATITUD": float,
    "LONGITUD": float,
    "VALOR": float,
    "DATA_HORA": "datetime64[us]",
}

# Meta schema after transform_datetime (DATA+HORA replaced by DATA_HORA)
meta_datetime = {
    "CODI EOI": int,
    "NOM ESTACIO": str,
    "MAGNITUD": int,
    "CONTAMINANT": str,
    "UNITATS": str,
    "TIPUS ESTACIO": str,
    "AREA URBANA": str,
    "CODI INE": int,
    "MUNICIPI": str,
    "CODI COMARCA": int,
    "NOM COMARCA": str,
    "ALTITUD": int,
    "LATITUD": float,
    "LONGITUD": float,
    "VALOR": float,
    "DATA_HORA": "datetime64[us]",
}

# Meta schema after input_missing_data (final bronze output)
meta_bronze = {
    "CODI EOI": int,
    "NOM ESTACIO": str,
    "MAGNITUD": int,
    "CONTAMINANT": str,
    "UNITATS": str,
    "TIPUS ESTACIO": str,
    "AREA URBANA": str,
    "CODI INE": int,
    "MUNICIPI": str,
    "CODI COMARCA": int,
    "NOM COMARCA": str,
    "ALTITUD": float,
    "LATITUD": float,
    "LONGITUD": float,
    "VALOR": float,
    "DATA_HORA": "datetime64[us]",
}
