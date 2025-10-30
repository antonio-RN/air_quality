# Air quality analysis

## Introduction

This is an exploratory analysis of air quality reports for Catalonia region, updated as of 14/05/2025. 
Data is downloaded from the [open data portal](https://administraciodigital.gencat.cat/ca/dades/dades-obertes/inici/index.html#googtrans(ca|en)) 
of Catalan Government (Generalitat de Catalunya), and includes hourly air quality metrics as well as 
geospatial information of the capture points.

The objective of this analysis is to find the biggest contributors to air pollution in Catalonia for the time period of the data. In order to get to this, both time evolution and geographic position will be taken into account.

## Project workflow

The analysis will be structured around a [kedro](https://docs.kedro.org/en/stable/introduction/index.html) 
basic workflow, written in Python and uses the following tools / packages:

- uv (package dependency manager)
- quarto (report renderer)
- pandas (data wrangling)
- altair (data visualization)
- geopandas (geospatial analysis)
- darts (time series analysis)

The diagram of the different processes applied to the data is shown below:

- [x] Data ingestion and type checking: reading the raw CSV file, converting to appropriate data types, saving data to a parquet file.
- [x] Missing data handling: analyzing missing data and handling it properly (removing or imputing), saving "bronze" data to a parquet file.
- [ ] General exploration: checking data overview to spot inconsistencies and get a general grasp of the data "shape".
- [ ] Feature creation: adding new features or characteristics based on geographic knowledge or specific thematic knowledge (air pollution).
- [ ] Time evolution: checking trends through time in the general dataset.
- [ ] Geographic inequalities: checking differences between geographic points and their relationship to them.
- [ ] Combined analysis: mixing time evolution and geographic inequialities to identify broader patterns.

**WIP --> to be updated as the analysis progresses.**

Head over to `notebooks/air_quality_exploration.html` in order to see the step-by-step analysis of the data. In a future, a complete kedro run will be available to re-run the analysis at your own machine.
