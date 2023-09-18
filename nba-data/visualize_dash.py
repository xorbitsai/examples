import sys

import plotly.express as px
import xorbits.pandas as pd
from dash import Dash, Input, Output, callback, dcc, html

from visualize_plotly import (_get_data_and_clean, _get_player_score,
                              top_20_player_names)

shot_detail_path = sys.argv[1]
stat_detail_path = sys.argv[2]
shot_detail, stat_detail = _get_data_and_clean(shot_detail_path, stat_detail_path)

player_score = _get_player_score(shot_detail, stat_detail)
res1 = player_score.groupby(["GAME_YEAR", "PLAYER1_NAME"], as_index=True, sort=False)[
    ["PLAYER_SCORE"]
].sum()
res2 = player_score.groupby(["GAME_YEAR", "PLAYER1_NAME"], as_index=True, sort=False)[
    ["GAME_ID"]
].nunique()
res = pd.concat([res1, res2], axis=1).reset_index()
res["AVG"] = res["PLAYER_SCORE"] / res["GAME_ID"]
res = res.drop(columns=["PLAYER_SCORE", "GAME_ID"])

years = pd.DataFrame(
    {
        "GAME_YEAR": [y for y in range(1996, 2024)] * 20,
        "PLAYER1_NAME": top_20_player_names * 28,
    }
)
res = years.merge(res, how="left", on=["GAME_YEAR", "PLAYER1_NAME"])
res["AVG"] = res["AVG"].fillna(0.0)
res = res.sort_values("GAME_YEAR")
print(res)


app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1(
            children="Average points per game by NBA players over 20+ years",
            style={"textAlign": "center"},
        ),
        dcc.Dropdown(
            top_20_player_names, top_20_player_names[0], id="dropdown-selection"
        ),
        dcc.Graph(id="graph-content"),
    ]
)


@callback(Output("graph-content", "figure"), Input("dropdown-selection", "value"))
def update_graph(value):
    dff = res[res["PLAYER1_NAME"] == value]
    fig = px.scatter(dff, x=dff["GAME_YEAR"], y=dff["AVG"])
    fig.update_layout(xaxis={"tickmode": "linear", "tick0": 0, "dtick": 1})
    fig.update_traces(mode="markers+lines")
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
