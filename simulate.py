import math
import random
import numpy as np


def create_schedule(num_teams):
    """
    Creates a schedule for each team in the league with num_teams in the
    league. The schedule is 17 weeks long and returns a list of lists where
    each nested list is a team's schedule for the season. Each team should
    only play each other team a maximum of ceiling(17 / num_teams) times.

    Teams are represented by integers that represent the index of that team's
    schedule in the list returned i.e. 0, 1, 2, ...
    """
    all_schedules = []
    choices = []
    max_same_opponent = math.ceil(17 / num_teams)
    for i in range(num_teams):
        choices += [i] * max_same_opponent
    for team in range(num_teams):
        temp_choices = choices.copy()
        for i in range(max_same_opponent):
            temp_choices.remove(team)
        team_schedule = random.sample(temp_choices, 17)
        all_schedules.append(team_schedule)
    return all_schedules


def ideal_simulate_season(schedule, roster):
    """
    Simulates a 17 week long fantasy football season given a list of the
    schedule and roster for each team in the league by using the ideal roster
    for each team in each week of the season. This means that each week each
    team's best roster is used.

    Returns the win/loss/tie record for each team as well as the total points
    scored by each team.

    Uses a standard 1 QB, 2 RB, 2 WR, 1 TE, 1 FLEX (RB/WR/TE), 1 DST, 1 K
    format for each week's roster.
    """
    # Get the points for each team
    weekly_points = []
    for team in roster:
        # Get the ideal points for each team for each week in the season
        team_results = [0] * 17

        best_qb = [0] * 17
        best_rb1 = [0] * 17
        best_rb2 = [0] * 17
        best_wr1 = [0] * 17
        best_wr2 = [0] * 17
        best_te = [0] * 17
        best_flex = [0] * 17
        best_dst = [0] * 17
        best_k = [0] * 17
        for week in range(17):
            # Get best qb points from roster for each week of the season
            for qb in team["qb"]:
                if qb[week] > best_qb[week]:
                    best_qb[week] = qb[week]

            # Get best rb points from roster for each week of the season
            for rb in team["rb"]:
                if rb[week] > best_rb1[week]:
                    if best_rb2[week] > best_flex[week]:
                        best_flex[week] = best_rb2[week]
                    best_rb2[week] = best_rb1[week]
                    best_rb1[week] = rb[week]
                elif rb[week] > best_rb2[week]:
                    if best_rb2[week] > best_flex[week]:
                        best_flex[week] = best_rb2[week]
                    best_rb2[week] = rb[week]
                elif rb[week] > best_flex[week]:
                    best_flex[week] = rb[week]

            # Get best wr points from roster for each week of the season
            for wr in team["wr"]:
                if wr[week] > best_wr1[week]:
                    if best_wr2[week] > best_flex[week]:
                        best_flex[week] = best_wr2[week]
                    best_wr2[week] = best_wr1[week]
                    best_wr1[week] = wr[week]
                elif wr[week] > best_wr2[week]:
                    if best_wr2[week] > best_flex[week]:
                        best_flex[week] = best_wr2[week]
                    best_wr2[week] = wr[week]
                elif wr[week] > best_flex[week]:
                    best_flex[week] = wr[week]

            # Get best te points from roster for each week of the season
            for te in team["te"]:
                if te[week] > best_te[week]:
                    if best_te[week] > best_flex[week]:
                        best_flex[week] = best_te[week]
                    best_te[week] = te[week]
                elif te[week] > best_flex[week]:
                    best_flex[week] = te[week]

            # Get best dst points from roster for each week of the season
            for dst in team["dst"]:
                if dst[week] > best_dst[week]:
                    best_dst[week] = dst[week]

            # Get best k points from roster for each week of the season
            for k in team["k"]:
                if k[week] > best_k[week]:
                    best_k[week] = k[week]

            # Get total team points for each week of the season
            team_results[week] += best_qb[week] + best_rb1[week] + best_rb2[week] + best_wr1[week] + \
                best_wr2[week] + best_te[week] + \
                best_flex[week] + best_dst[week] + best_k[week]

        weekly_points.append(team_results)

    # Get the number of wins, ties, and losses for each team for the season
    num_teams = len(schedule)
    team_wins = [0] * num_teams
    team_ties = [0] * num_teams
    team_losses = [0] * num_teams
    for team_id in range(num_teams):
        team_schedule = schedule[team_id]
        for week in range(17):
            opponent_id = team_schedule[week]
            if weekly_points[team_id][week] > weekly_points[opponent_id][week]:
                team_wins[team_id] += 1
            elif weekly_points[team_id][week] < weekly_points[opponent_id][week]:
                team_losses[team_id] += 1
            else:
                team_ties[team_id] += 1

    # Get the total points for the season for each team
    team_total_points = [0] * num_teams
    for team_id in range(num_teams):
        team_total_points[team_id] = np.sum(weekly_points[team_id])

    # Return a dictionary of the results
    result_dict = {}
    result_dict["Wins"] = team_wins
    result_dict["Losses"] = team_losses
    result_dict["Ties"] = team_ties
    result_dict["Total Points Scored"] = team_total_points
    return result_dict
