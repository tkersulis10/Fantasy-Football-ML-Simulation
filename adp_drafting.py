import time
from selenium import webdriver
from bs4 import BeautifulSoup
import pickle5
import numpy as np
import get_nn_data
import simulate2
import copy


class Triple:
    def __init__(self, player_name, player_pick, player_gamelog):
        self.player_name = player_name
        self.player_pick = player_pick
        self.player_gamelog = player_gamelog

    def __hash__(self):
        return hash(self.player_name)

    def __eq__(self, other):
        # print("other: " + str(other))
        return self.player_name == other.player_name

    def __repr__(self):
        return self.player_name

    def __str__(self):
        return self.player_name

    def get_gamelog(self):
        return self.player_gamelog

    def get_round(self):
        return self.player_pick[0]

    def get_name(self):
        return self.player_name


def get_adp_data():
    """
    Get the 2018 - 2022 NFL season ADP data.
    """
    # Chrome webdriver options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    # Different driver paths per computer
    driver_path = "Program Files\Google\Chrome\Application\chrome.exe"
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    # driver = webdriver.Chrome(options=options)

    bestball_format = [False, True]
    for bestball in bestball_format:
        yearly_adps = {'2018': [], '2019': [],
                       '2020': [], '2021': [], '2022': []}
        for year in range(2018, 2023):
            # Load the URL in the webdriver
            if bestball == False:
                adp_url = "https://www.fantasypros.com/nfl/adp/half-point-ppr-overall.php?year=" + \
                    str(year)
            else:
                adp_url = "https://www.fantasypros.com/nfl/adp/best-ball-overall.php?year=" + \
                    str(year)

            driver.get(adp_url)
            time.sleep(2)

            # Parse the HTML content
            htmlSource = driver.page_source
            soup = BeautifulSoup(htmlSource, "html.parser")

            results = soup.find(
                "div", class_="mobile-table").find("tbody")
            players = results.find_all("tr")

            with open('nn_data/player_gamelogs.pkl', 'rb') as inp:
                player_gamelog_dict = pickle5.load(inp)

            adp_list = []
            for player in players:
                stats = player.find_all("td")
                player_name = stats[1].find("a").text
                if player_name != "":
                    player_pos = stats[2].text[:2]
                    if bestball:
                        player_avg_adp = stats[7].text
                    else:
                        player_avg_adp = stats[6].text

                    invalid_pos = False
                    if player_pos == "QB":
                        fp_index = 19
                    elif player_pos == "RB":
                        fp_index = 16
                    elif player_pos == "WR":
                        fp_index = 16
                    elif player_pos == "TE":
                        fp_index = 16
                    elif player_pos == "DS":
                        player_pos = "DST"
                        fp_index = 10
                    elif player_pos[:1] == "K":
                        player_pos = "K"
                        fp_index = 14
                    else:
                        invalid_pos = True

                    if not invalid_pos:
                        player_name_lookup = player_name.split(" ")
                        player_name_lookup = get_nn_data.check_name(
                            player_name_lookup)
                        player_name_lookup = player_name_lookup[0].title(
                        ) + player_name_lookup[1].title() + str(year)

                        try:
                            player_gamelog = player_gamelog_dict[player_name_lookup]
                            fantasy_pts = []
                            for game in player_gamelog:
                                if game['Game OPP'] == 'BYE Week':
                                    fantasy_pts.append(0)
                                else:
                                    fantasy_pts.append(game['Fantasy  Points'])
                        except KeyError:
                            fp_link = stats[1].find("a").get("href")
                            if player_pos == "DST":
                                link = fp_link[11:]
                            else:
                                link = fp_link[13:]
                            gamelog_url = "https://www.fantasypros.com/nfl/games/" + \
                                link + "?season=" + str(year) + "&scoring=HALF"

                            driver.get(gamelog_url)
                            time.sleep(2)

                            # Parse the HTML content
                            htmlSource = driver.page_source
                            soup = BeautifulSoup(htmlSource, "html.parser")

                            # Get player fantasy gamelog
                            results = soup.find("div", class_="mobile-table")
                            games = results.find("tbody").find_all("tr")

                            fantasy_pts = []
                            if len(games) == 1:
                                fantasy_pts = [0] * 18
                            else:
                                for game in games:
                                    stats = game.find_all("td")
                                    if len(stats) < 3:
                                        fantasy_pts.append(0)
                                    else:
                                        try:
                                            fantasy_pts.append(
                                                stats[fp_index].text)
                                        except:
                                            fantasy_pts.append(0)
                            print(player_name)
                            print(fantasy_pts)

                        adp_list.append(
                            (player_name, player_pos, player_avg_adp, fantasy_pts))

            yearly_adps[str(year)] = adp_list

        if bestball:
            output_file = 'adp_data/bestball_adp_data'
        else:
            output_file = 'adp_data/adp_data'
        with open(output_file + '.pkl', 'wb') as outp:
            pickle5.dump(yearly_adps, outp, pickle5.HIGHEST_PROTOCOL)
        with open(output_file + '.txt', "w") as file:
            for year in yearly_adps:
                file.write(year + ":\n")
                file.write(str(yearly_adps[year]) + "\n\n")


def simulate_drafts_store_data(num_drafts, num_teams, num_rounds, bestball):
    """
    Simulate drafts.

    num_drafts is the number of drafts to simulate.
    num_teams is the number of teams in the league.
    num_rounds is the number of rounds in the draft.
    bestball is True if this league is in bestball format, False otherwise.
    """
    # if bestball == True:
    #     with open('adp_data/bestball_adp_data.pkl', 'rb') as inp:
    #         adp_values = pickle5.load(inp)
    # else:
    #     with open('adp_data/adp_data.pkl', 'rb') as inp:
    #         adp_values = pickle5.load(inp)
    # with open('adp_data/qb_adp_data.pkl', 'rb') as inp:
    #     qb_values = pickle5.load(inp)
    # with open('adp_data/rb_adp_data.pkl', 'rb') as inp:
    #     rb_values = pickle5.load(inp)
    # with open('adp_data/wr_adp_data.pkl', 'rb') as inp:
    #     wr_values = pickle5.load(inp)
    # with open('adp_data/te_adp_data.pkl', 'rb') as inp:
    #     te_values = pickle5.load(inp)
    # with open('adp_data/dst_adp_data.pkl', 'rb') as inp:
    #     dst_values = pickle5.load(inp)
    # with open('adp_data/k_adp_data.pkl', 'rb') as inp:
    #     k_values = pickle5.load(inp)

    # roster = {}
    # roster["qb"] = set()
    # roster["rb"] = set()
    # roster["wr"] = set()
    # roster["te"] = set()
    # roster["dst"] = set()
    # roster["k"] = set()
    # if bestball == False:
    #     roster["dst"].add(Triple("Streaming", None, np.array([5] * 17)))
    #     roster["k"].add(Triple("Streaming", None, np.array([6] * 17)))

    # position_min = ['rb', 'rb', 'rb', 'wr', 'wr', 'wr', 'te', 'qb']
    # if bestball == True:
    #     position_min += ['qb', 'te']
    # else:
    #     position_min += ['dst', 'k']
    # best_teams = {'2018': [], '2019': [], '2020': [], '2021': [], '2022': []}
    # for year in range(2018, 2023):
    #     for draft in range(num_drafts):
    #         print(draft)
    #         year_adps = copy.deepcopy(adp_values[str(year)])
    #         team_rosters = [copy.deepcopy(roster)
    #                         for i in range(num_teams)]
    #         qb_players = copy.deepcopy(qb_values)
    #         rb_players = copy.deepcopy(rb_values)
    #         wr_players = copy.deepcopy(wr_values)
    #         te_players = copy.deepcopy(te_values)
    #         dst_players = copy.deepcopy(dst_values)
    #         k_players = copy.deepcopy(k_values)
    #         team_position_mins = [copy.deepcopy(
    #             position_min) for i in range(num_teams)]
    #         current_round = 1
    #         current_pick = 0
    #         end_draft = False

    #         while not end_draft:
    #             # satisfactory_pick = False
    #             # while not satisfactory_pick:
    #             #     random_pick = np.random.geometric(p=0.25) - 1
    #             #     while random_pick >= len(year_adps):
    #             #         random_pick = np.random.geometric(p=0.25) - 1
    #             #     player_picked = year_adps[random_pick]
    #             #     player_pos = player_picked[1].lower()
    #             #     if player_pos in team_position_mins[current_pick]:
    #             #         team_position_mins[current_pick].remove(player_pos)
    #             #     if num_rounds - current_round >= len(team_position_mins[current_pick]):
    #             #         satisfactory_pick = True

    #             random_pick = np.random.geometric(p=0.25) - 1
    #             while random_pick >= len(year_adps):
    #                 random_pick = np.random.geometric(p=0.25) - 1
    #             player_picked = year_adps[random_pick]
    #             player_pos = player_picked[1].lower()
    #             if player_pos in team_position_mins[current_pick]:
    #                 team_position_mins[current_pick].remove(player_pos)
    #             if num_rounds - current_round < len(team_position_mins[current_pick]):
    #                 positions_needed = []
    #                 if "qb" in team_position_mins[current_pick]:
    #                     positions_needed += qb_players[str(year)]
    #                 if "rb" in team_position_mins[current_pick]:
    #                     positions_needed += rb_players[str(year)]
    #                 if "wr" in team_position_mins[current_pick]:
    #                     positions_needed += wr_players[str(year)]
    #                 if "te" in team_position_mins[current_pick]:
    #                     positions_needed += te_players[str(year)]
    #                 if "dst" in team_position_mins[current_pick]:
    #                     positions_needed += dst_players[str(year)]
    #                 if "k" in team_position_mins[current_pick]:
    #                     positions_needed += k_players[str(year)]
    #                 positions_needed.sort(key=lambda x: x[2])
    #                 random_pick = np.random.geometric(p=0.5) - 1
    #                 while random_pick >= len(positions_needed):
    #                     random_pick = np.random.geometric(p=0.5) - 1
    #                 player_picked = positions_needed[random_pick]
    #                 player_pos = player_picked[1].lower()
    #                 team_position_mins[current_pick].remove(player_pos)
    #                 year_adps.remove(player_picked)
    #             else:
    #                 year_adps.pop(random_pick)

    #             if player_pos == "qb":
    #                 qb_players[str(year)].remove(player_picked)
    #             elif player_pos == "rb":
    #                 rb_players[str(year)].remove(player_picked)
    #             elif player_pos == "wr":
    #                 wr_players[str(year)].remove(player_picked)
    #             elif player_pos == "te":
    #                 te_players[str(year)].remove(player_picked)
    #             elif player_pos == "dst":
    #                 dst_players[str(year)].remove(player_picked)
    #             elif player_pos == "k":
    #                 k_players[str(year)].remove(player_picked)

    #             try:
    #                 team_rosters[current_pick][player_pos].add(Triple(
    #                     player_picked[0], (current_round, current_pick), convert_gamelog(player_picked[3])))
    #             except:
    #                 team_rosters[current_pick]['k'].add(Triple(
    #                     player_picked[0], (current_round, current_pick), convert_gamelog(player_picked[3])))
    #             if current_round % 2 == 1:
    #                 if current_pick < num_teams - 1:
    #                     current_pick += 1
    #                 else:
    #                     current_round += 1
    #                     if current_round > num_rounds:
    #                         end_draft = True
    #             else:
    #                 if current_pick > 0:
    #                     current_pick -= 1
    #                 else:
    #                     current_round += 1
    #                     if current_round > num_rounds:
    #                         end_draft = True

    #         team_pts = [0] * num_teams
    #         best_team_pts = -100
    #         for team in range(num_teams):
    #             if bestball == True:
    #                 season_pts = simulate2.team_pts_scored_3wr(
    #                     team_rosters[team])
    #             else:
    #                 season_pts = simulate2.team_pts_scored(team_rosters[team])
    #             team_pts[team] = season_pts
    #             if season_pts > best_team_pts:
    #                 best_team_pts = season_pts
    #                 best_team_roster = team_rosters[team]

    #         best_teams[str(year)].append((best_team_roster, best_team_pts))

    #     best_teams[str(year)].sort(key=lambda x: x[1], reverse=True)

    if bestball == True:
        output_file = 'adp_data/bestball_adp_draft_results.pkl'
    else:
        output_file = 'adp_data/adp_draft_results.pkl'
    with open(output_file, 'wb') as outp:
        simulate_season(
            False, outp, num_drafts, num_teams, num_rounds, bestball)


def simulate_season_display_draft(num_teams, num_rounds, bestball):
    """
    Simulates one draft/season and outputs the draft results.
    """
    if bestball == True:
        output_file = 'adp_data/bestball_adp_draft_results.txt'
    else:
        output_file = 'adp_data/adp_draft_results.txt'
    with open(output_file, "w") as file:
        simulate_season(True, file, 1, num_teams, num_rounds, bestball)


def simulate_season(draft_output, file, num_drafts, num_teams, num_rounds, bestball):
    """
    Simulates a season.

    draft_output is True if the draft picks and results should be written to file.
    """
    if bestball == True:
        with open('adp_data/bestball_adp_data.pkl', 'rb') as inp:
            adp_values = pickle5.load(inp)
        file_prefix = 'bestball_'
    else:
        with open('adp_data/adp_data.pkl', 'rb') as inp:
            adp_values = pickle5.load(inp)
        file_prefix = ''

    with open('adp_data/' + file_prefix + 'qb_adp_data.pkl', 'rb') as inp:
        qb_values = pickle5.load(inp)
    with open('adp_data/' + file_prefix + 'rb_adp_data.pkl', 'rb') as inp:
        rb_values = pickle5.load(inp)
    with open('adp_data/' + file_prefix + 'wr_adp_data.pkl', 'rb') as inp:
        wr_values = pickle5.load(inp)
    with open('adp_data/' + file_prefix + 'te_adp_data.pkl', 'rb') as inp:
        te_values = pickle5.load(inp)
    with open('adp_data/dst_adp_data.pkl', 'rb') as inp:
        dst_values = pickle5.load(inp)
    with open('adp_data/k_adp_data.pkl', 'rb') as inp:
        k_values = pickle5.load(inp)

    roster = {}
    roster["qb"] = set()
    roster["rb"] = set()
    roster["wr"] = set()
    roster["te"] = set()
    roster["dst"] = set()
    roster["k"] = set()
    if bestball == False:
        roster["dst"].add(Triple("Streaming", None, np.array([6] * 17)))
        roster["k"].add(Triple("Streaming", None, np.array([7.5] * 17)))

    position_min = ['rb', 'rb', 'rb', 'wr', 'wr', 'wr', 'te', 'qb']
    if bestball == True:
        position_min += ['qb', 'te']
        position_limit = {'qb': 0.2, 'rb': 0.75, 'wr': 0.75, 'te': 0.2}
    else:
        position_min += ['dst', 'k']
        position_limit = {'qb': 0.15, 'rb': 0.75,
                          'wr': 0.75, 'te': 0.15, 'dst': 0.2, 'k': 0.2}
    # best_teams = {'2018': [], '2019': [],
    #               '2020': [], '2021': [], '2022': []}
    for year in range(2018, 2023):
        year_leagues = []
        for draft in range(num_drafts):
            print(draft)
            if draft_output:
                file.write(str(year) + ":\n")
            year_adps = copy.deepcopy(adp_values[str(year)])
            team_rosters = [copy.deepcopy(roster)
                            for i in range(num_teams)]
            qb_players = copy.deepcopy(qb_values)
            rb_players = copy.deepcopy(rb_values)
            wr_players = copy.deepcopy(wr_values)
            te_players = copy.deepcopy(te_values)
            dst_players = copy.deepcopy(dst_values)
            k_players = copy.deepcopy(k_values)
            team_position_mins = [copy.deepcopy(
                position_min) for i in range(num_teams)]
            current_round = 1
            current_pick = 0
            end_draft = False

            while not end_draft:
                # satisfactory_pick = False
                # while not satisfactory_pick:
                #     random_pick = np.random.geometric(p=0.25) - 1
                #     while random_pick >= len(year_adps):
                #         random_pick = np.random.geometric(p=0.25) - 1
                #     player_picked = year_adps[random_pick]
                #     player_pos = player_picked[1].lower()
                #     if player_pos in team_position_mins[current_pick]:
                #         team_position_mins[current_pick].remove(player_pos)
                #     if num_rounds - current_round >= len(team_position_mins[current_pick]):
                #         satisfactory_pick = True

                random_pick = np.random.geometric(p=0.25) - 1
                while random_pick >= len(year_adps):
                    random_pick = np.random.geometric(p=0.25) - 1
                player_picked = year_adps[random_pick]
                player_pos = player_picked[1].lower()

                if current_round > 3:
                    if len(team_rosters[current_pick][player_pos]) / (current_round - 1) >= position_limit[player_pos]:
                        random_pick = np.random.geometric(p=0.25) - 1
                        while random_pick >= len(year_adps):
                            random_pick = np.random.geometric(p=0.25) - 1
                        player_picked = year_adps[random_pick]
                        player_pos = player_picked[1].lower()

                if player_pos in team_position_mins[current_pick]:
                    team_position_mins[current_pick].remove(player_pos)
                if num_rounds - current_round < len(team_position_mins[current_pick]):
                    positions_needed = []
                    if "qb" in team_position_mins[current_pick]:
                        positions_needed += qb_players[str(year)]
                    if "rb" in team_position_mins[current_pick]:
                        positions_needed += rb_players[str(year)]
                    if "wr" in team_position_mins[current_pick]:
                        positions_needed += wr_players[str(year)]
                    if "te" in team_position_mins[current_pick]:
                        positions_needed += te_players[str(year)]
                    if "dst" in team_position_mins[current_pick]:
                        positions_needed += dst_players[str(year)]
                    if "k" in team_position_mins[current_pick]:
                        positions_needed += k_players[str(year)]
                    if len(positions_needed) == 0:
                        random_pick = np.random.geometric(p=0.25) - 1
                        while random_pick >= len(year_adps):
                            random_pick = np.random.geometric(p=0.25) - 1
                        player_picked = year_adps[random_pick]
                        player_pos = player_picked[1].lower()
                        year_adps.pop(random_pick)
                    else:
                        positions_needed.sort(key=lambda x: x[2])
                        random_pick = np.random.geometric(p=0.5) - 1
                        while random_pick >= len(positions_needed):
                            random_pick = np.random.geometric(p=0.5) - 1
                        player_picked = positions_needed[random_pick]
                        player_pos = player_picked[1].lower()
                        team_position_mins[current_pick].remove(player_pos)
                        year_adps.remove(player_picked)
                else:
                    year_adps.pop(random_pick)

                if player_pos == "qb":
                    qb_players[str(year)].remove(player_picked)
                elif player_pos == "rb":
                    rb_players[str(year)].remove(player_picked)
                elif player_pos == "wr":
                    wr_players[str(year)].remove(player_picked)
                elif player_pos == "te":
                    te_players[str(year)].remove(player_picked)
                elif player_pos == "dst":
                    dst_players[str(year)].remove(player_picked)
                elif player_pos == "k":
                    k_players[str(year)].remove(player_picked)

                if draft_output:
                    file.write("Round " + str(current_round) + ", pick " +
                               str(current_pick) + ": " + player_picked[0] + ", " + player_pos + "\n")
                try:
                    team_rosters[current_pick][player_pos].add(Triple(
                        player_picked[0], (current_round, current_pick), convert_gamelog(player_picked[3])))
                except:
                    team_rosters[current_pick]['k'].add(Triple(
                        player_picked[0], (current_round, current_pick), convert_gamelog(player_picked[3])))
                if current_round % 2 == 1:
                    if current_pick < num_teams - 1:
                        current_pick += 1
                    else:
                        current_round += 1
                        if current_round > num_rounds:
                            end_draft = True
                else:
                    if current_pick > 0:
                        current_pick -= 1
                    else:
                        current_round += 1
                        if current_round > num_rounds:
                            end_draft = True

            if draft_output:
                file.write("\nPoints Scored:\n")
                for team in range(num_teams):
                    if bestball == True:
                        season_pts = simulate2.team_pts_scored_3wr(
                            team_rosters[team])
                    else:
                        season_pts = simulate2.team_pts_scored(
                            team_rosters[team])
                    file.write("Team " + str(team) + ": " +
                               str(season_pts) + "\n")
                file.write("\n")
            else:
                league_teams = []
                for team in range(num_teams):
                    if bestball == True:
                        season_pts = simulate2.team_pts_scored_3wr(
                            team_rosters[team])
                    else:
                        season_pts = simulate2.team_pts_scored(
                            team_rosters[team])
                    league_teams.append((team_rosters[team], season_pts))
                league_teams.sort(key=lambda x: x[1], reverse=True)
                year_leagues.append(league_teams)

                # team_pts = [0] * num_teams
                # best_team_pts = -100
                # for team in range(num_teams):
                #     if bestball == True:
                #         season_pts = simulate2.team_pts_scored_3wr(
                #             team_rosters[team])
                #     else:
                #         season_pts = simulate2.team_pts_scored(
                #             team_rosters[team])
                #     team_pts[team] = season_pts
                #     if season_pts > best_team_pts:
                #         best_team_pts = season_pts
                #         best_team_roster = team_rosters[team]
                # best_teams[str(year)].append(
                #     (best_team_roster, best_team_pts))

        if not draft_output:
            pickle5.dump(year_leagues, file, pickle5.HIGHEST_PROTOCOL)
        # if not draft_output:
            # best_teams[str(year)].sort(key=lambda x: x[1], reverse=True)

    # return best_teams


def convert_gamelog(gamelog_list):
    """
    Convert the gamelog list to a numpy array.
    """
    number_games = len(gamelog_list)
    if number_games < 17:
        gamelog_list += [0.0] * (17 - number_games)
    return np.array([0.0 if i == "-" else float(i) for i in gamelog_list])


def adp_data_to_bestball():
    """
    Convert adp data to best ball data (no defense and kicker).
    """
    with open('adp_data/bestball_adp_data.pkl', 'rb') as inp:
        adp_values = pickle5.load(inp)
    bestball_adp_values = {'2018': [], '2019': [],
                           '2020': [], '2021': [], '2022': []}
    for year in adp_values:
        for player in adp_values[year]:
            player_name = player[0]
            player_pos = player[1]
            if player_pos != "DST" and player_pos != "K":
                if player_name == "David Johnson" and year == '2018':
                    bestball_adp_values[year].insert(
                        2, (player_name, player_pos, '3.0', player[3]))
                elif player_name == "Mike Williams" and year == '2019':
                    bestball_adp_values[year].insert(
                        53, (player_name, player_pos, '53.5', player[3]))
                else:
                    bestball_adp_values[year].append(player)

    with open('adp_data/bestball_adp_data.pkl', 'wb') as outp:
        pickle5.dump(bestball_adp_values, outp, pickle5.HIGHEST_PROTOCOL)
    with open('adp_data/bestball_adp_data.txt', "w") as file:
        for year in bestball_adp_values:
            file.write(year + ":\n")
            file.write(str(bestball_adp_values[year]) + "\n\n")


def get_positional_adps(bestball):
    """
    Store positional adps in files.
    """
    if bestball:
        with open('adp_data/bestball_adp_data.pkl', 'rb') as inp:
            adp_values = pickle5.load(inp)
    else:
        with open('adp_data/adp_data.pkl', 'rb') as inp:
            adp_values = pickle5.load(inp)

    qb_values = {'2018': [], '2019': [], '2020': [], '2021': [], '2022': []}
    rb_values = {'2018': [], '2019': [], '2020': [], '2021': [], '2022': []}
    wr_values = {'2018': [], '2019': [], '2020': [], '2021': [], '2022': []}
    te_values = {'2018': [], '2019': [], '2020': [], '2021': [], '2022': []}
    dst_values = {'2018': [], '2019': [], '2020': [], '2021': [], '2022': []}
    k_values = {'2018': [], '2019': [], '2020': [], '2021': [], '2022': []}

    for year in adp_values:
        for player in adp_values[year]:
            player_pos = player[1]
            if player_pos == 'QB':
                qb_values[year].append(player)
            elif player_pos == 'RB':
                rb_values[year].append(player)
            elif player_pos == 'WR':
                wr_values[year].append(player)
            elif player_pos == 'TE':
                te_values[year].append(player)
            elif player_pos == 'DST':
                dst_values[year].append(player)
            elif player_pos == 'K':
                k_values[year].append(player)

    if bestball:
        with open('adp_data/bestball_qb_adp_data.pkl', 'wb') as outp:
            pickle5.dump(qb_values, outp, pickle5.HIGHEST_PROTOCOL)
        with open('adp_data/bestball_qb_adp_data.txt', "w") as file:
            for year in qb_values:
                file.write(year + ":\n")
                file.write(str(qb_values[year]) + "\n\n")

        with open('adp_data/bestball_rb_adp_data.pkl', 'wb') as outp:
            pickle5.dump(rb_values, outp, pickle5.HIGHEST_PROTOCOL)
        with open('adp_data/bestball_rb_adp_data.txt', "w") as file:
            for year in rb_values:
                file.write(year + ":\n")
                file.write(str(rb_values[year]) + "\n\n")

        with open('adp_data/bestball_wr_adp_data.pkl', 'wb') as outp:
            pickle5.dump(wr_values, outp, pickle5.HIGHEST_PROTOCOL)
        with open('adp_data/bestball_wr_adp_data.txt', "w") as file:
            for year in wr_values:
                file.write(year + ":\n")
                file.write(str(wr_values[year]) + "\n\n")

        with open('adp_data/bestball_te_adp_data.pkl', 'wb') as outp:
            pickle5.dump(te_values, outp, pickle5.HIGHEST_PROTOCOL)
        with open('adp_data/bestball_te_adp_data.txt', "w") as file:
            for year in te_values:
                file.write(year + ":\n")
                file.write(str(te_values[year]) + "\n\n")
    else:
        with open('adp_data/qb_adp_data.pkl', 'wb') as outp:
            pickle5.dump(qb_values, outp, pickle5.HIGHEST_PROTOCOL)
        with open('adp_data/qb_adp_data.txt', "w") as file:
            for year in qb_values:
                file.write(year + ":\n")
                file.write(str(qb_values[year]) + "\n\n")

        with open('adp_data/rb_adp_data.pkl', 'wb') as outp:
            pickle5.dump(rb_values, outp, pickle5.HIGHEST_PROTOCOL)
        with open('adp_data/rb_adp_data.txt', "w") as file:
            for year in rb_values:
                file.write(year + ":\n")
                file.write(str(rb_values[year]) + "\n\n")

        with open('adp_data/wr_adp_data.pkl', 'wb') as outp:
            pickle5.dump(wr_values, outp, pickle5.HIGHEST_PROTOCOL)
        with open('adp_data/wr_adp_data.txt', "w") as file:
            for year in wr_values:
                file.write(year + ":\n")
                file.write(str(wr_values[year]) + "\n\n")

        with open('adp_data/te_adp_data.pkl', 'wb') as outp:
            pickle5.dump(te_values, outp, pickle5.HIGHEST_PROTOCOL)
        with open('adp_data/te_adp_data.txt', "w") as file:
            for year in te_values:
                file.write(year + ":\n")
                file.write(str(te_values[year]) + "\n\n")

        with open('adp_data/dst_adp_data.pkl', 'wb') as outp:
            pickle5.dump(dst_values, outp, pickle5.HIGHEST_PROTOCOL)
        with open('adp_data/dst_adp_data.txt', "w") as file:
            for year in dst_values:
                file.write(year + ":\n")
                file.write(str(dst_values[year]) + "\n\n")

        with open('adp_data/k_adp_data.pkl', 'wb') as outp:
            pickle5.dump(k_values, outp, pickle5.HIGHEST_PROTOCOL)
        with open('adp_data/k_adp_data.txt', "w") as file:
            for year in k_values:
                file.write(year + ":\n")
                file.write(str(k_values[year]) + "\n\n")


def get_statistics(bestball):
    """
    Get the statistics for the drafts.

    bestball is True if this league is in bestball format, False otherwise.
    """
    if bestball == True:
        input_file = 'adp_data/bestball_adp_draft_results.pkl'
        # with open('adp_data/bestball_adp_draft_results.pkl', 'rb') as inp:
        #     draft_results = pickle5.load(inp)
    else:
        input_file = 'adp_data/adp_draft_results.pkl'
        # with open('adp_data/adp_draft_results.pkl', 'rb') as inp:
        #     draft_results = pickle5.load(inp)

    stat_dict = {'# QBs': 0, '# RBs': 0, '# WRs': 0, '# TEs': 0,
                 'first QB drafted': 0, 'first RB drafted': 0,
                 'first WR drafted': 0, 'first TE drafted': 0,
                 '1st round QB': 0, '1st round RB': 0,
                 '1st round WR': 0, '1st round TE': 0,
                 '2nd round QB': 0, '2nd round RB': 0,
                 '2nd round WR': 0, '2nd round TE': 0,
                 '3rd round QB': 0, '3rd round RB': 0,
                 '3rd round WR': 0, '3rd round TE': 0,
                 '4th round QB': 0, '4th round RB': 0,
                 '4th round WR': 0, '4th round TE': 0,
                 '5th round QB': 0, '5th round RB': 0,
                 '5th round WR': 0, '5th round TE': 0,
                 '6th round QB': 0, '6th round RB': 0,
                 '6th round WR': 0, '6th round TE': 0,
                 '7th round QB': 0, '7th round RB': 0,
                 '7th round WR': 0, '7th round TE': 0,
                 '8th round QB': 0, '8th round RB': 0,
                 '8th round WR': 0, '8th round TE': 0,
                 '9th round QB': 0, '9th round RB': 0,
                 '9th round WR': 0, '9th round TE': 0,
                 '10th round QB': 0, '10th round RB': 0,
                 '10th round WR': 0, '10th round TE': 0,
                 'RB, RB': 0, 'RB, WR': 0, 'WR, RB': 0,
                 'WR, WR': 0, 'RB, TE': 0, 'RB, QB': 0,
                 'TE, RB': 0, 'QB, RB': 0, 'WR, TE': 0,
                 'WR, QB': 0, 'TE, WR': 0, 'QB, WR': 0,
                 'TE, TE': 0, 'TE, QB': 0, 'QB, TE': 0,
                 'QB, QB': 0, 'Zero RB': 0, 'Zero WR': 0,
                 'Early QB (1-3)': 0, 'Mid QB (4-7)': 0, 'Late QB (8+)': 0,
                 'Early TE (1-3)': 0, 'Mid TE (4-7)': 0, 'Late TE (8+)': 0,
                 'Hero RB': 0}
    winning_yearly_stats = {'2018': copy.deepcopy(stat_dict), '2019': copy.deepcopy(stat_dict), '2020': copy.deepcopy(
        stat_dict), '2021': copy.deepcopy(stat_dict), '2022': copy.deepcopy(stat_dict)}
    top200_yearly_stats = {'2018': copy.deepcopy(stat_dict), '2019': copy.deepcopy(stat_dict), '2020': copy.deepcopy(
        stat_dict), '2021': copy.deepcopy(stat_dict), '2022': copy.deepcopy(stat_dict)}
    average_yearly_stats = {'2018': copy.deepcopy(stat_dict), '2019': copy.deepcopy(stat_dict), '2020': copy.deepcopy(
        stat_dict), '2021': copy.deepcopy(stat_dict), '2022': copy.deepcopy(stat_dict)}
    top200_player_stats = {'2018': {}, '2019': {},
                           '2020': {}, '2021': {}, '2022': {}}
    winning_player_stats = {'2018': {}, '2019': {},
                            '2020': {}, '2021': {}, '2022': {}}
    qb_player_stats = {'2018': {}, '2019': {},
                       '2020': {}, '2021': {}, '2022': {}}
    rb_player_stats = {'2018': {}, '2019': {},
                       '2020': {}, '2021': {}, '2022': {}}
    wr_player_stats = {'2018': {}, '2019': {},
                       '2020': {}, '2021': {}, '2022': {}}
    te_player_stats = {'2018': {}, '2019': {},
                       '2020': {}, '2021': {}, '2022': {}}
    dst_player_stats = {'2018': {}, '2019': {},
                        '2020': {}, '2021': {}, '2022': {}}
    k_player_stats = {'2018': {}, '2019': {},
                      '2020': {}, '2021': {}, '2022': {}}
    with open(input_file, 'rb') as inp:
        for int_year in range(2018, 2023):
            print(int_year)
            year_draft_results = pickle5.load(inp)
            league_count = len(year_draft_results)
            year = str(int_year)
            count = 0

            league_winners = []
            for league in year_draft_results:
                league_winners.append(league[0])
            league_winners.sort(key=lambda x: x[1], reverse=True)
            top200_points = league_winners[199][1]

            for league in year_draft_results:
                print(count)
                count += 1
                num_teams = len(league)
                for team_index in range(num_teams):
                    current_team = league[team_index]
                    roster = current_team[0]
                    roster_qbs = roster['qb']
                    roster_rbs = roster['rb']
                    roster_wrs = roster['wr']
                    roster_tes = roster['te']
                    roster_dsts = roster['dst']
                    roster_ks = roster['k']

                    if team_index == 0:
                        if current_team[1] >= top200_points:
                            yearly_stats = top200_yearly_stats
                            player_stats = top200_player_stats
                        else:
                            yearly_stats = winning_yearly_stats
                            player_stats = winning_player_stats
                    else:
                        yearly_stats = average_yearly_stats

                    num_qbs = len(roster_qbs)
                    yearly_stats[year]['# QBs'] += num_qbs
                    num_rbs = len(roster_rbs)
                    yearly_stats[year]['# RBs'] += num_rbs
                    num_wrs = len(roster_wrs)
                    yearly_stats[year]['# WRs'] += num_wrs
                    num_tes = len(roster_tes)
                    yearly_stats[year]['# TEs'] += num_tes

                    first_qb = float('inf')
                    first_rb = float('inf')
                    first_wr = float('inf')
                    first_te = float('inf')
                    round_one_pick = ''
                    round_two_pick = ''
                    for qb in roster_qbs:
                        round = qb.get_round()
                        name = qb.get_name()
                        if team_index == 0:
                            try:
                                player_stats[year][(name, "QB")] = (player_stats[year][(
                                    name, "QB")][0] + 1, player_stats[year][(name, "QB")][1] + 1)
                            except KeyError:
                                player_stats[year][(name, "QB")] = (1, 1)
                        else:
                            try:
                                player_stats[year][(name, "QB")] = (
                                    player_stats[year][(name, "QB")][0], player_stats[year][(name, "QB")][1] + 1)
                            except KeyError:
                                player_stats[year][(name, "QB")] = (0, 1)
                        if round < first_qb:
                            first_qb = round
                        if round == 1:
                            yearly_stats[year]['1st round QB'] += 1
                            round_one_pick = 'QB'
                        elif round == 2:
                            yearly_stats[year]['2nd round QB'] += 1
                            round_two_pick = 'QB'
                        elif round == 3:
                            yearly_stats[year]['3rd round QB'] += 1
                        elif round == 4:
                            yearly_stats[year]['4th round QB'] += 1
                        elif round == 5:
                            yearly_stats[year]['5th round QB'] += 1
                        elif round == 6:
                            yearly_stats[year]['6th round QB'] += 1
                        elif round == 7:
                            yearly_stats[year]['7th round QB'] += 1
                        elif round == 8:
                            yearly_stats[year]['8th round QB'] += 1
                        elif round == 9:
                            yearly_stats[year]['9th round QB'] += 1
                        elif round == 10:
                            yearly_stats[year]['10th round QB'] += 1
                    yearly_stats[year]['first QB drafted'] += first_qb

                    for rb in roster_rbs:
                        round = rb.get_round()
                        name = rb.get_name()
                        if team_index == 0:
                            try:
                                player_stats[year][(name, "RB")] = (player_stats[year][(
                                    name, "RB")][0] + 1, player_stats[year][(name, "RB")][1] + 1)
                            except KeyError:
                                player_stats[year][(name, "RB")] = (1, 1)
                        else:
                            try:
                                player_stats[year][(name, "RB")] = (
                                    player_stats[year][(name, "RB")][0], player_stats[year][(name, "RB")][1] + 1)
                            except KeyError:
                                player_stats[year][(name, "RB")] = (0, 1)
                        if round < first_rb:
                            first_rb = round
                        if round == 1:
                            yearly_stats[year]['1st round RB'] += 1
                            round_one_pick = 'RB'
                        elif round == 2:
                            yearly_stats[year]['2nd round RB'] += 1
                            round_two_pick = 'RB'
                        elif round == 3:
                            yearly_stats[year]['3rd round RB'] += 1
                        elif round == 4:
                            yearly_stats[year]['4th round RB'] += 1
                        elif round == 5:
                            yearly_stats[year]['5th round RB'] += 1
                        elif round == 6:
                            yearly_stats[year]['6th round RB'] += 1
                        elif round == 7:
                            yearly_stats[year]['7th round RB'] += 1
                        elif round == 8:
                            yearly_stats[year]['8th round RB'] += 1
                        elif round == 9:
                            yearly_stats[year]['9th round RB'] += 1
                        elif round == 10:
                            yearly_stats[year]['10th round RB'] += 1
                    yearly_stats[year]['first RB drafted'] += first_rb

                    for wr in roster_wrs:
                        round = wr.get_round()
                        name = wr.get_name()
                        if team_index == 0:
                            try:
                                player_stats[year][(name, "WR")] = (player_stats[year][(
                                    name, "WR")][0] + 1, player_stats[year][(name, "WR")][1] + 1)
                            except KeyError:
                                player_stats[year][(name, "WR")] = (1, 1)
                        else:
                            try:
                                player_stats[year][(name, "WR")] = (
                                    player_stats[year][(name, "WR")][0], player_stats[year][(name, "WR")][1] + 1)
                            except KeyError:
                                player_stats[year][(name, "WR")] = (0, 1)
                        if round < first_wr:
                            first_wr = round
                        if round == 1:
                            yearly_stats[year]['1st round WR'] += 1
                            round_one_pick = 'WR'
                        elif round == 2:
                            yearly_stats[year]['2nd round WR'] += 1
                            round_two_pick = 'WR'
                        elif round == 3:
                            yearly_stats[year]['3rd round WR'] += 1
                        elif round == 4:
                            yearly_stats[year]['4th round WR'] += 1
                        elif round == 5:
                            yearly_stats[year]['5th round WR'] += 1
                        elif round == 6:
                            yearly_stats[year]['6th round WR'] += 1
                        elif round == 7:
                            yearly_stats[year]['7th round WR'] += 1
                        elif round == 8:
                            yearly_stats[year]['8th round WR'] += 1
                        elif round == 9:
                            yearly_stats[year]['9th round WR'] += 1
                        elif round == 10:
                            yearly_stats[year]['10th round WR'] += 1
                    yearly_stats[year]['first WR drafted'] += first_wr

                    for te in roster_tes:
                        round = te.get_round()
                        name = te.get_name()
                        if team_index == 0:
                            try:
                                player_stats[year][(name, "TE")] = (player_stats[year][(
                                    name, "TE")][0] + 1, player_stats[year][(name, "TE")][1] + 1)
                            except KeyError:
                                player_stats[year][(name, "TE")] = (1, 1)
                        else:
                            try:
                                player_stats[year][(name, "TE")] = (
                                    player_stats[year][(name, "TE")][0], player_stats[year][(name, "TE")][1] + 1)
                            except KeyError:
                                player_stats[year][(name, "TE")] = (0, 1)
                        if round < first_te:
                            first_te = round
                        if round == 1:
                            yearly_stats[year]['1st round TE'] += 1
                            round_one_pick = 'TE'
                        elif round == 2:
                            yearly_stats[year]['2nd round TE'] += 1
                            round_two_pick = 'TE'
                        elif round == 3:
                            yearly_stats[year]['3rd round TE'] += 1
                        elif round == 4:
                            yearly_stats[year]['4th round TE'] += 1
                        elif round == 5:
                            yearly_stats[year]['5th round TE'] += 1
                        elif round == 6:
                            yearly_stats[year]['6th round TE'] += 1
                        elif round == 7:
                            yearly_stats[year]['7th round TE'] += 1
                        elif round == 8:
                            yearly_stats[year]['8th round TE'] += 1
                        elif round == 9:
                            yearly_stats[year]['9th round TE'] += 1
                        elif round == 10:
                            yearly_stats[year]['10th round TE'] += 1
                    yearly_stats[year]['first TE drafted'] += first_te

                    for dst in roster_dsts:
                        name = dst.get_name()
                        if team_index == 0:
                            try:
                                player_stats[year][(name, "DST")] = (player_stats[year][(
                                    name, "DST")][0] + 1, player_stats[year][(name, "DST")][1] + 1)
                            except KeyError:
                                player_stats[year][(name, "DST")] = (1, 1)
                        else:
                            try:
                                player_stats[year][(name, "DST")] = (
                                    player_stats[year][(name, "DST")][0], player_stats[year][(name, "DST")][1] + 1)
                            except KeyError:
                                player_stats[year][(name, "DST")] = (0, 1)

                    for k in roster_ks:
                        name = k.get_name()
                        if team_index == 0:
                            try:
                                player_stats[year][(name, "K")] = (player_stats[year][(
                                    name, "K")][0] + 1, player_stats[year][(name, "K")][1] + 1)
                            except KeyError:
                                player_stats[year][(name, "K")] = (1, 1)
                        else:
                            try:
                                player_stats[year][(name, "K")] = (
                                    player_stats[year][(name, "K")][0], player_stats[year][(name, "K")][1] + 1)
                            except KeyError:
                                player_stats[year][(name, "K")] = (0, 1)

                    if round_one_pick == 'RB':
                        if round_two_pick == 'RB':
                            yearly_stats[year]['RB, RB'] += 1
                        elif round_two_pick == 'WR':
                            yearly_stats[year]['RB, WR'] += 1
                        elif round_two_pick == 'TE':
                            yearly_stats[year]['RB, TE'] += 1
                        elif round_two_pick == 'QB':
                            yearly_stats[year]['RB, QB'] += 1
                    elif round_one_pick == 'WR':
                        if round_two_pick == 'RB':
                            yearly_stats[year]['WR, RB'] += 1
                        elif round_two_pick == 'WR':
                            yearly_stats[year]['WR, WR'] += 1
                        elif round_two_pick == 'TE':
                            yearly_stats[year]['WR, TE'] += 1
                        elif round_two_pick == 'QB':
                            yearly_stats[year]['WR, QB'] += 1
                    elif round_one_pick == 'TE':
                        if round_two_pick == 'RB':
                            yearly_stats[year]['TE, RB'] += 1
                        elif round_two_pick == 'WR':
                            yearly_stats[year]['TE, WR'] += 1
                        elif round_two_pick == 'TE':
                            yearly_stats[year]['TE, TE'] += 1
                        elif round_two_pick == 'QB':
                            yearly_stats[year]['TE, QB'] += 1
                    elif round_one_pick == 'QB':
                        if round_two_pick == 'RB':
                            yearly_stats[year]['QB, RB'] += 1
                        elif round_two_pick == 'WR':
                            yearly_stats[year]['QB, WR'] += 1
                        elif round_two_pick == 'TE':
                            yearly_stats[year]['QB, TE'] += 1
                        elif round_two_pick == 'QB':
                            yearly_stats[year]['QB, QB'] += 1

                    if first_qb < 4:
                        yearly_stats[year]['Early QB (1-3)'] += 1
                    elif first_qb < 8:
                        yearly_stats[year]['Mid QB (4-7)'] += 1
                    else:
                        yearly_stats[year]['Late QB (8+)'] += 1
                    if first_te < 4:
                        yearly_stats[year]['Early TE (1-3)'] += 1
                    elif first_te < 8:
                        yearly_stats[year]['Mid TE (4-7)'] += 1
                    else:
                        yearly_stats[year]['Late TE (8+)'] += 1
                    if first_rb > 4:
                        yearly_stats[year]['Zero RB'] += 1
                    if first_wr > 4:
                        yearly_stats[year]['Zero WR'] += 1
                    if first_rb == 1:
                        second_rb = float('inf')
                        for rb in roster_rbs:
                            round = rb.get_round()
                            if round != 1:
                                if round < second_rb:
                                    second_rb = round
                        if second_rb > 5:
                            yearly_stats[year]['Hero RB'] += 1

            for stat in average_yearly_stats[year]:
                average_yearly_stats[year][stat] = (
                    average_yearly_stats[year][stat] + winning_yearly_stats[year][stat] + top200_yearly_stats[year][stat]) / (league_count * num_teams)
            for stat in winning_yearly_stats[year]:
                winning_yearly_stats[year][stat] = (
                    winning_yearly_stats[year][stat] + top200_yearly_stats[year][stat]) / league_count
            for stat in top200_yearly_stats[year]:
                top200_yearly_stats[year][stat] /= 200
            delete_player_list = []
            for player in winning_player_stats[year]:
                try:
                    num_wins = winning_player_stats[year][player][0] + \
                        top200_player_stats[year][player][0]
                    num_drafts = winning_player_stats[year][player][1] + \
                        top200_player_stats[year][player][1]
                except KeyError:
                    num_wins = winning_player_stats[year][player][0]
                    num_drafts = winning_player_stats[year][player][1]
                if player[1] == 'K':
                    min_num_drafts = 500
                else:
                    min_num_drafts = 200
                if num_drafts >= min_num_drafts:
                    winning_player_stats[year][player] = num_wins / num_drafts
                else:
                    delete_player_list.append(player)
            for player in delete_player_list:
                del winning_player_stats[year][player]
            for player in top200_player_stats[year]:
                top200_player_stats[year][player] = top200_player_stats[year][player][0] / \
                    top200_player_stats[year][player][1]

            winning_player_stats[year] = dict(
                sorted(winning_player_stats[year].items(), key=lambda x: x[1], reverse=True))
            for player in winning_player_stats[year]:
                player_name = player[0]
                player_position = player[1]
                if player_position == "QB":
                    position_player_dict = qb_player_stats
                elif player_position == "RB":
                    position_player_dict = rb_player_stats
                elif player_position == "WR":
                    position_player_dict = wr_player_stats
                elif player_position == "TE":
                    position_player_dict = te_player_stats
                elif player_position == "DST":
                    position_player_dict = dst_player_stats
                else:
                    position_player_dict = k_player_stats
                try:
                    position_player_dict[year][player_name] = (
                        winning_player_stats[year][player], top200_player_stats[year][player])
                except KeyError:
                    position_player_dict[year][player_name] = (
                        winning_player_stats[year][player], 0)

    top200_overall_stats = copy.deepcopy(stat_dict)
    for stat in top200_overall_stats:
        top200_overall_stats[stat] = (top200_yearly_stats['2018'][stat] + top200_yearly_stats['2019'][stat] +
                                      top200_yearly_stats['2020'][stat] + top200_yearly_stats['2021'][stat] +
                                      top200_yearly_stats['2022'][stat]) / 5

    winning_overall_stats = copy.deepcopy(stat_dict)
    for stat in winning_overall_stats:
        winning_overall_stats[stat] = (winning_yearly_stats['2018'][stat] + winning_yearly_stats['2019'][stat] +
                                       winning_yearly_stats['2020'][stat] + winning_yearly_stats['2021'][stat] +
                                       winning_yearly_stats['2022'][stat]) / 5

    average_overall_stats = copy.deepcopy(stat_dict)
    for stat in average_overall_stats:
        average_overall_stats[stat] = (average_yearly_stats['2018'][stat] + average_yearly_stats['2019'][stat] +
                                       average_yearly_stats['2020'][stat] + average_yearly_stats['2021'][stat] +
                                       average_yearly_stats['2022'][stat]) / 5

    if bestball == True:
        output_file_name = 'adp_data/bestball_data_analysis.txt'
        output_player_file_name = 'adp/bestball_player_analysis.txt'
    else:
        output_file_name = 'adp_data/data_analysis.txt'
        output_player_file_name = 'adp_data/player_analysis.txt'
        ranking_file_name = 'adp_data/eos_rankings.pkl'
    with open(output_file_name, "w") as file:
        for year in winning_yearly_stats:
            file.write(year + ":\n")
            file.write(
                "Top 200 teams' stats (left) vs league's highest scoring team's stats (middle) vs average team's stats (right):\n")
            for stat in winning_yearly_stats[year]:
                file.write(stat + ": " +
                           str(top200_yearly_stats[year][stat]) + ", " + str(winning_yearly_stats[year][stat]) + ", " + str(average_yearly_stats[year][stat]) + "\n")
            file.write("\n")
            file.write(
                "Percentage of time player seen on top 200 team (left) and league's highest scoring team (right):\n")
            for player in winning_player_stats[year]:
                try:
                    file.write(player[0] + ": " + str(top200_player_stats[year][player]) + ", " +
                               str(winning_player_stats[year][player]) + "\n")
                except KeyError:
                    file.write(player[0] + ": 0, " +
                               str(winning_player_stats[year][player]) + "\n")
            file.write("\n")
        file.write("Overall: \n")
        file.write(
            "Top 200 teams' stats (left) vs league's highest scoring team's stats (middle) vs average team's stats (right):\n")
        for stat in winning_overall_stats:
            file.write(stat + ": " + str(top200_overall_stats[stat]) + ", " + str(winning_overall_stats[stat]) + ", " + str(
                average_overall_stats[stat]) + "\n")
    with open(output_player_file_name, "w") as file:
        with open(ranking_file_name, 'rb') as inp:
            ranking_dict = pickle5.load(inp)
        for year in winning_player_stats:
            file.write(year + ":\n")
            file.write("Top player ownership (all positions):\n")
            file.write("Player, ownership, ADP, Ranking\n")
            for player in winning_player_stats[year]:
                # try:
                #     file.write(player[0] + ", " + player[1] + ": " + str(top200_player_stats[year][player]) + ", " +
                #                str(winning_player_stats[year][player]) + "\n")
                # except KeyError:
                player_name = player[0]
                player_position = player[1]
                player_ownership = winning_player_stats[year][player]
                if player_ownership < 0.1:
                    player_ownership = str(player_ownership)
                    player_ownership = player_ownership[3:4] + \
                        "." + player_ownership[4:6]
                else:
                    player_ownership = str(player_ownership)
                    player_ownership = player_ownership[2:4] + \
                        "." + player_ownership[4:6]
                if player_name != "Streaming":
                    file.write(player_name + ": " + player_ownership + "%, " + player_position + ranking_dict[year][player_position][player_name][0] +
                               ", " + player_position + ranking_dict[year][player_position][player_name][1] + "\n")
            file.write('\n')
            position_player_list = [qb_player_stats, rb_player_stats,
                                    wr_player_stats, te_player_stats, dst_player_stats, k_player_stats]
            for position_dict in position_player_list:
                if position_dict == qb_player_stats:
                    player_position = "QB"
                elif position_dict == rb_player_stats:
                    player_position = "RB"
                elif position_dict == wr_player_stats:
                    player_position = "WR"
                elif position_dict == te_player_stats:
                    player_position = "TE"
                elif position_dict == dst_player_stats:
                    player_position = "DST"
                else:
                    player_position = "K"
                file.write(player_position + ":\n")
                for player in position_dict[year]:
                    player_ownership = position_dict[year][player][0]
                    if player_ownership < 0.1:
                        player_ownership = str(player_ownership)
                        player_ownership = player_ownership[3:4] + \
                            "." + player_ownership[4:6]
                    else:
                        player_ownership = str(player_ownership)
                        player_ownership = player_ownership[2:4] + \
                            "." + player_ownership[4:6]
                    if player != "Streaming":
                        file.write(player + ": " + player_ownership + "%, " + player_position + ranking_dict[year][player_position][player][0] +
                                   ", " + player_position + ranking_dict[year][player_position][player][1] + "\n")
                file.write("\n")


def get_position_rankings(bestball):
    """
    Store the adp and end of season rankings.
    """
    if bestball:
        file_prefix = 'bestball_'
    else:
        file_prefix = ''
    with open('adp_data/' + file_prefix + 'qb_adp_data.pkl', 'rb') as inp:
        qb_values = pickle5.load(inp)
    with open('adp_data/' + file_prefix + 'rb_adp_data.pkl', 'rb') as inp:
        rb_values = pickle5.load(inp)
    with open('adp_data/' + file_prefix + 'wr_adp_data.pkl', 'rb') as inp:
        wr_values = pickle5.load(inp)
    with open('adp_data/' + file_prefix + 'te_adp_data.pkl', 'rb') as inp:
        te_values = pickle5.load(inp)
    with open('adp_data/dst_adp_data.pkl', 'rb') as inp:
        dst_values = pickle5.load(inp)
    with open('adp_data/k_adp_data.pkl', 'rb') as inp:
        k_values = pickle5.load(inp)

    # Chrome webdriver options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    # Different driver paths per computer
    driver_path = "Program Files\Google\Chrome\Application\chrome.exe"
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    # driver = webdriver.Chrome(options=options)

    year_dict = {"QB": {}, "RB": {}, "WR": {}, "TE": {}, "DST": {}, "K": {}}
    ranking_dict = {'2018': copy.deepcopy(year_dict), '2019': copy.deepcopy(year_dict), '2020': copy.deepcopy(
        year_dict), '2021': copy.deepcopy(year_dict), '2022': copy.deepcopy(year_dict)}
    for int_year in range(2018, 2023):
        year = str(int_year)
        for position in ranking_dict[year]:
            # Load the URL in the webdriver
            ranking_url = "https://www.fantasypros.com/nfl/stats/" + \
                position.lower() + ".php?year=" + year + "&scoring=HALF"
            driver.get(ranking_url)
            time.sleep(2)

            # Parse the HTML content
            htmlSource = driver.page_source
            soup = BeautifulSoup(htmlSource, "html.parser")

            if position == "DST" or position == "K":
                results = soup.find(
                    "div", class_="mobile-table").find("tbody")
            else:
                results = soup.find(
                    "div", class_="mobile-table double-header").find("tbody")
            players = results.find_all("tr")

            if position == "QB":
                fantasy_pts_index = 15
                value_dict = qb_values
            elif position == "RB":
                fantasy_pts_index = 15
                value_dict = rb_values
            elif position == "WR":
                fantasy_pts_index = 14
                value_dict = wr_values
            elif position == "TE":
                fantasy_pts_index = 14
                value_dict = te_values
            elif position == "K":
                fantasy_pts_index = 14
                value_dict = k_values
            elif position == "DST":
                fantasy_pts_index = 10
                value_dict = dst_values

            for player in players:
                stats = player.find_all("td")
                ranking = stats[0].text
                name = stats[1].find("a").text
                if position == "DST":
                    name += " DST"
                fantasy_pts = stats[fantasy_pts_index].text
                ranking_dict[year][position][name] = (ranking, fantasy_pts)

            index = 1
            for player in value_dict[year]:
                try:
                    previous_tuple = ranking_dict[year][position][player[0]]
                    ranking_dict[year][position][player[0]] = (
                        str(index), previous_tuple[0], previous_tuple[1])
                except KeyError:
                    ranking_dict[year][position][player[0]] = (
                        str(index), 'DNP', '0')
                index += 1
    with open('adp_data/eos_rankings.pkl', 'wb') as outp:
        pickle5.dump(ranking_dict, outp, pickle5.HIGHEST_PROTOCOL)


# get_adp_data()
# adp_data_to_bestball()
# get_positional_adps(False)
# get_positional_adps(True)
# simulate_drafts_store_data(20000, 12, 16, False)
# simulate_drafts_store_data(20000, 12, 18, True)
# get_position_rankings(False)
get_statistics(False)
# get_statistics(True)
# simulate_season_display_draft(12, 16, False)
# simulate_season_display_draft(12, 18, True)
