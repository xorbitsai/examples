import os
import sys

import plotly.express as px
import xorbits.pandas as pd
from dash import Dash, Input, Output, callback, dcc, html

from visualize_plotly import _get_data_and_clean, _get_player_score

res_csv_path = os.path.join(os.path.dirname(__file__), "__tmp__.csv")

if not os.path.exists(res_csv_path):

    def _get_player_ids(shot_detail):
        res = shot_detail[["PLAYER_ID", "PLAYER_NAME"]].drop_duplicates()
        res.columns = ["PLAYER1_ID", "PLAYER_NAME"]
        return res

    shot_detail_path = sys.argv[1]
    stat_detail_path = sys.argv[2]
    shot_detail, stat_detail = _get_data_and_clean(shot_detail_path, stat_detail_path)

    player_ids = _get_player_ids(shot_detail)
    player_stats = _get_player_score(shot_detail, stat_detail, player_ids)

    def handle(x):
        is_home = x["HTM"] == x["PLAYER1_TEAM_ABBREVIATION"]
        game_score = x["SCORE"]
        player_score = x["PLAYER_SCORE"]
        hvs = game_score.split("-")
        if len(hvs) == 2:
            visitor_s, home_s = hvs
            visitor_s, home_s = int(visitor_s), int(home_s)
            self_team_score = home_s if is_home else visitor_s
            other_team_score = visitor_s if is_home else home_s
            before_score = self_team_score - player_score
            if other_team_score >= before_score:
                return player_score
            else:
                return 0 - player_score
        else:
            return player_score

    player_stats["PLAYER_HANDLE_SCORE"] = player_stats.apply(handle, axis=1)
    # print(player_stats)

    def tmp1(x):
        y = x["PLAYER_HANDLE_SCORE"]
        games = x["GAME_ID"].nunique()
        play_score_positive = y[y > 0].abs().sum() / games
        return play_score_positive

    def tmp2(x):
        y = x["PLAYER_HANDLE_SCORE"]
        games = x["GAME_ID"].nunique()
        play_score_positive = y[y < 0].abs().sum() / games
        return play_score_positive

    def tmp3(x):
        return x["GAME_ID"].nunique()

    res1 = player_stats.groupby(
        ["PLAYER1_NAME", "GAME_YEAR"], as_index=True, sort=False
    )[["PLAYER_HANDLE_SCORE", "GAME_ID"]].apply(tmp1)
    res1.name = "POSITIVE_SCORE"

    res2 = player_stats.groupby(
        ["PLAYER1_NAME", "GAME_YEAR"], as_index=True, sort=False
    )[["PLAYER_HANDLE_SCORE", "GAME_ID"]].apply(tmp2)
    res2.name = "NEGATIVE_SCORE"

    res3 = player_stats.groupby(
        ["PLAYER1_NAME", "GAME_YEAR"], as_index=True, sort=False
    )[["GAME_ID"]].apply(tmp3)
    res3.name = "GAMES_CNT"
    res = pd.concat([res1, res2, res3], axis=1)
    res = res.reset_index()

    def tmp4(x):
        y = x[x["GAMES_CNT"] >= 20]
        return y.nlargest(
            20, columns=["POSITIVE_SCORE", "NEGATIVE_SCORE", "GAMES_CNT"], keep="all"
        )

    res = res.groupby("GAME_YEAR", as_index=False, sort=False).apply(tmp4)
    res = res.sort_values("GAME_YEAR")
    res.to_csv(res_csv_path)

df = pd.read_csv(res_csv_path)

app = Dash(__name__)

app.layout = html.Div(
    [
        html.H1(
            children="The NBA Key Player by Year",
            style={"textAlign": "center"},
        ),
        dcc.Dropdown(df["GAME_YEAR"].unique(), 1996, id="dropdown-selection"),
        dcc.Graph(id="graph-content"),
    ]
)


@callback(Output("graph-content", "figure"), Input("dropdown-selection", "value"))
def update_graph(value):
    dff = df[df["GAME_YEAR"] == value]
    fig = px.scatter(
        dff,
        x="POSITIVE_SCORE",
        y="NEGATIVE_SCORE",
        size="GAMES_CNT",
        text="PLAYER1_NAME",
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(
        xaxis_title="Average points scored when the team is behind",
        yaxis_title="Average points scored when the team is ahead",
        title_text="Scoring performance in different team situations",
    )
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
