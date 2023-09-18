import sys

import plotly.express as px
import plotly.graph_objects as go
import xorbits.pandas as pd
from plotly.subplots import make_subplots

top_20_player_names = [
    "Michael Jordan",
    "LeBron James",
    "Shaquille O'Neal",
    "Tim Duncan",
    "Kobe Bryant",
    "Kevin Durant",
    "Stephen Curry",
    "Kevin Garnett",
    "Dirk Nowitzki",
    "Giannis Antetokounmpo",
    "Dwyane Wade",
    "Chris Paul",
    "James Harden",
    "Kawhi Leonard",
    "Jason Kidd",
    "Steve Nash",
    "Allen Iverson",
    "Russell Westbrook",
    "Paul Pierce",
    "Ray Allen",
]


def three_pt_trends(shot_detail):
    def t_3pt(x):
        return x[x.str.startswith("3PT")].count()

    res = (
        shot_detail.groupby("GAME_YEAR", as_index=True, sort=False)["SHOT_TYPE"]
        .agg([t_3pt, "count"])
        .sort_index()
    )
    res["rate"] = res["t_3pt"] / res["count"]

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Scatter(
            x=pd.Series(res.index), y=res["t_3pt"], name="Number of 3pt field goals"
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=pd.Series(res.index), y=res["count"], name="Number of field goals"
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=pd.Series(res.index), y=res["rate"], name="Percentage of 3pt field goals"
        ),
        secondary_y=True,
    )

    fig.update_layout(
        xaxis_title="Year", xaxis={"tickmode": "linear", "tick0": 0, "dtick": 1}
    )
    fig.update_traces(mode="markers+lines")

    # Add figure title
    fig.update_layout(title_text="NBA 3PT Field Goal Trends")

    # Set y-axes titles
    fig.update_yaxes(title_text="Number of field goals", secondary_y=False)
    fig.update_yaxes(title_text="Percentage of 3PT field goals", secondary_y=True)

    fig.show()


def three_pt_player(shot_detail):
    def three_pt_total(x):
        return len(x[x["SHOT_TYPE"].str.startswith("3PT")])

    def three_pt_made_total(x):
        x = x[x["SHOT_MADE_FLAG"] == 1]
        x = x[x["SHOT_TYPE"].str.startswith("3PT")]
        return len(x)

    def three_pt_rate(x):
        total = three_pt_total(x)
        return three_pt_made_total(x) / total if total != 0 else 0

    _three_pt_made = shot_detail.groupby(
        "PLAYER_NAME",
        as_index=True,
        sort=False,
    ).apply(three_pt_made_total)

    _three_pt_total = shot_detail.groupby(
        "PLAYER_NAME",
        as_index=True,
        sort=False,
    ).apply(three_pt_total)

    _three_pt_rate = shot_detail.groupby(
        "PLAYER_NAME",
        as_index=True,
        sort=False,
    ).apply(three_pt_rate)

    res = pd.concat([_three_pt_made, _three_pt_total, _three_pt_rate], axis=1)
    res.columns = ["three_pt_made", "three_pt_total", "three_pt_rate"]
    res = res.nlargest(
        5, ["three_pt_made", "three_pt_total", "three_pt_rate"], keep="all"
    )

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Bar(
            x=pd.Series(res.index),
            y=res["three_pt_made"],
            offsetgroup=0,
            name="Count of made 3pt field goals",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=pd.Series(res.index),
            y=res["three_pt_total"],
            offsetgroup=1,
            name="Total count of 3pt field goals",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Bar(
            x=pd.Series(res.index),
            y=res["three_pt_rate"],
            offsetgroup=2,
            name="3pt field goal percentage",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title_text="NBA Best 3PT Field Goal Shooter", xaxis_title="Player Name"
    )

    # Set y-axes titles
    fig.update_yaxes(title_text="Number of 3pt field goals", secondary_y=False)
    fig.update_yaxes(title_text="3pt field goal percentage", secondary_y=True)

    fig.show()


def _get_player_score(shot_detail, stat_detail):
    player_names = shot_detail[["PLAYER_ID", "PLAYER_NAME"]].drop_duplicates()
    player_ids = player_names[player_names["PLAYER_NAME"].isin(top_20_player_names)]
    player_ids["PLAYER1_ID"] = player_ids["PLAYER_ID"]
    player_ids["PLAYER2_ID"] = player_ids["PLAYER_ID"]
    player_ids["PLAYER3_ID"] = player_ids["PLAYER_ID"]

    player_stats = stat_detail.merge(
        player_ids[["PLAYER1_ID"]], how="inner", on="PLAYER1_ID"
    )

    # add home and visitor info
    HV_info = shot_detail[["GAME_ID", "HTM", "VTM"]].drop_duplicates()
    player_stats = player_stats.merge(HV_info, how="left", on="GAME_ID")

    player_stats = player_stats[player_stats["SCOREMARGIN"] != -1000]

    event = shot_detail[
        ["GAME_ID", "GAME_EVENT_ID", "EVENT_TYPE", "SHOT_TYPE", "GAME_YEAR"]
    ]
    event.columns = ["GAME_ID", "EVENTNUM", "EVENT_TYPE", "SHOT_TYPE", "GAME_YEAR"]
    player_stats = player_stats.merge(event, how="left", on=["GAME_ID", "EVENTNUM"])
    player_stats["SHOT_TYPE"] = player_stats["SHOT_TYPE"].fillna("1PT Field Goal")

    def pt(x):
        shot_type = x["SHOT_TYPE"]
        return int(shot_type[0])

    player_stats["PLAYER_SCORE"] = player_stats.apply(pt, axis=1)
    return player_stats


def key_player(shot_detail, stat_detail):
    player_stats = _get_player_score(shot_detail, stat_detail)

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

    res1 = player_stats.groupby("PLAYER1_NAME", as_index=True, sort=False).apply(tmp1)
    res2 = player_stats.groupby("PLAYER1_NAME", as_index=True, sort=False).apply(tmp2)
    res3 = player_stats.groupby("PLAYER1_NAME", as_index=True, sort=False).apply(tmp3)
    res = pd.concat([res1, res2, res3], axis=1).reset_index()
    res.columns = ["PLAYER1_NAME", "P", "N", "C"]

    fig = px.scatter(res, x="P", y="N", size="C", text="PLAYER1_NAME")
    fig.update_traces(textposition="top center")
    fig.update_layout(
        xaxis_title="Average points scored when the team is behind",
        yaxis_title="Average points scored when the team is ahead",
        title_text="Scoring performance in different team situations",
    )
    fig.show()


def _get_data_and_clean(shot_detail_path, stat_detail_path):
    shot_detail = pd.read_csv(shot_detail_path)
    shot_detail["GAME_DATE"] = shot_detail["GAME_DATE"].fillna(00000000)
    shot_detail["SHOT_TYPE"] = shot_detail["SHOT_TYPE"].fillna("")
    shot_detail["GAME_YEAR"] = (shot_detail["GAME_DATE"] / 10000).astype("int")

    stat_detail = pd.read_csv(stat_detail_path)
    stat_detail["SCOREMARGIN"] = stat_detail["SCOREMARGIN"].fillna(-1000)
    stat_detail["SCORE"] = stat_detail["SCORE"].fillna("")
    return shot_detail, stat_detail


if __name__ == "__main__":
    shot_detail_path = sys.argv[1]
    stat_detail_path = sys.argv[2]
    _type = sys.argv[3]

    shot_detail, stat_detail = _get_data_and_clean(shot_detail_path, stat_detail_path)

    if _type == "key_player":
        key_player(shot_detail, stat_detail)
    elif _type == "3_pt_player":
        three_pt_player(shot_detail)
    elif _type == "3_pt_trend":
        three_pt_trends(shot_detail)
