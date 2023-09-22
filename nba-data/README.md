# Example for Xorbits with Plotly and Dash

## Prerequisite
- Xorbits >= 0.6.1
- Dash
- Plotly

## Datasets
You can download from [here](https://github.com/shufinskiy/nba_data).

Dataset contains play-by-play data from three sources: stats.nba.com, data.nba.com and pbpstats.com and also shots details. 

Dataset contains data from:
- season 1996/97 for stats.nba.com and shotdetails
- from season 2000/01 for pbpstats.com 
- from season 2016/17 for data.nba.com

## Xorbits with Plotly
Usage:
```shell
python visualize_plotly.py <shotdetail_dataset_path> <nbastats_dataset_path> <type_of_statistic>
```
- `<shotdetail_dataset_path>` is the path where the `shotdetail` dataset stores.
- `<nbastats_dataset_path>` is the path where the `nbastats` dataset stores.
- `<type_of_statistic>` can be:
    - `key_player`: show the scoring ability of 20 players in different team situations
    - `3_pt_player`: show the 5 best 3-point shooters from different dimensions
    - `3_pt_trend`: show total NBA 3-point shooting trends over 20+ years


## Xorbits with Dash
Usage:
```shell
python visualize_dash.py <shotdetail_dataset_path> <nbastats_dataset_path>
```
