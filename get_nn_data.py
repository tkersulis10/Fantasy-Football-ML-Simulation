import time
from selenium import webdriver
from bs4 import BeautifulSoup
import pickle5


def get_nn_team_data(fp_team_abbrev_dict, pfr_team_abbrev_dict):
    """
    Get the fantasy football advanced data for teams. fp_team_abbrev_dict and
    pfr_team_abbrev_dict are dictionaries where the keys are each team's
    abbreviation (i.e. SF) and the values are each team's full name (i.e. San
    Francisco 49ers) for fantasypros and pro football reference, respectively.
    """
    # Chrome webdriver options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    # Different driver paths per computer
    driver_path = "Program Files\Google\Chrome\Application\chrome.exe"
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    # driver = webdriver.Chrome(options=options)

    # Load the URL in the webdriver
    year = 2020
    team_dict = {}
    for year in range(2020, 2023):
        # URL for team targets
        team_target_url = "https://www.fantasypros.com/nfl/reports/targets-distribution/?year=" + \
            str(year) + "&start=1&end=18"
        driver.get(team_target_url)
        time.sleep(2)

        # Parse the HTML content
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource, "html.parser")

        results = soup.find(
            "div", class_="mobile-table").find("tbody")
        teams = results.find_all("tr")

        for team in teams:
            team_name = team.find("a").text + str(year)
            stat_list = team.find_all("td", class_="center")
            team_dict[team_name] = {}
            team_dict[team_name]["targets"] = [stat.text for stat in stat_list]

        # URL for fantasy points against
        fantasy_pts_against_url = "https://www.fantasypros.com/nfl/points-allowed.php?year=" + \
            str(year)
        driver.get(fantasy_pts_against_url)
        time.sleep(2)

        # Parse the HTML content
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource, "html.parser")

        results = soup.find(
            "div", class_="mobile-table").find("tbody")
        teams = results.find_all("tr")

        for team in teams:
            try:
                team_name = team.find("a").text + str(year)
                stat_list = team.find_all("td", class_="center")
                team_dict[team_name]["fantasy pts against"] = [
                    stat_list[i].text for i in range(1, len(stat_list), 2)]
            except:
                pass

        # URL for team's schedule
        schedule_url = "https://www.fantasypros.com/nfl/schedule.php?year" + \
            str(year)
        driver.get(schedule_url)
        time.sleep(2)

        # Parse the HTML content
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource, "html.parser")

        results = soup.find(
            "div", class_="inner")
        teams = results.find_all(
            "section", class_="team-schedule general-container")

        for team in teams:
            team_name = team.find(
                "h2", class_="team-schedule__heading").find("a").text + str(year)
            schedule_list = team.find("tbody").find(
                "tr", class_="tr team-schedule__tr").find_all("td")
            team_dict[team_name]["schedule"] = [fp_team_abbrev_dict[opp_team.find(
                "a").text] + str(year) for opp_team in schedule_list]

        # URL for team's roster
        for team in pfr_team_abbrev_dict:
            team_roster_url = "https://www.pro-football-reference.com/teams/" + \
                team + "/" + str(year) + "-snap-counts.htm"
            driver.get(team_roster_url)
            time.sleep(2)

            # Parse the HTML content
            htmlSource = driver.page_source
            soup = BeautifulSoup(htmlSource, "html.parser")

            results = soup.find("div", id="all_snap_counts").find(
                "div", class_="table_container is_setup").find("tbody")
            players = results.find_all("tr")

            team_dict[pfr_team_abbrev_dict[team] + str(year)]["roster"] = []
            for player in players:
                try:
                    player_stats = player.find_all("td")
                    for stat in player_stats:
                        stat_name = stat.get("data-stat")
                        if stat_name == "pos":
                            player_pos = stat.text
                        elif stat_name == "offense":
                            snap_num = stat.text
                        elif stat_name == "off_pct":
                            snap_pct = stat.text
                    if player_pos == "QB" or player_pos == "RB" or player_pos == "FB" or player_pos == "WR" or player_pos == "TE":
                        player_name = player.find("a").text
                        team_dict[pfr_team_abbrev_dict[team] +
                                  str(year)]["roster"].append((player_name, player_pos, snap_num, snap_pct))
                except:
                    pass

    with open('nn_data/team_stats.pkl', 'wb') as outp:
        pickle5.dump(team_dict, outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/team_stats.txt', "w") as file:
        for team in team_dict:
            file.write(team + ":\n")
            file.write(str(team_dict[team]) + "\n")


def get_nn_player_data(fp_team_abbrev_dict, pfr_team_abbrev_dict):
    # Chrome webdriver options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    # Different driver paths per computer
    driver_path = "Program Files\Google\Chrome\Application\chrome.exe"
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    # driver = webdriver.Chrome(options=options)

    # Load the URL in the webdriver
    year = 2020
    player_dict = {}
    for year in range(2020, 2023):
        # URL for players's stats
        for team in pfr_team_abbrev_dict:
            team_adv_stats_url = "https://www.pro-football-reference.com/teams/" + \
                team + "/" + str(year) + "_advanced.htm"
            driver.get(team_adv_stats_url)
            time.sleep(2)

            # Parse the HTML content
            htmlSource = driver.page_source
            soup = BeautifulSoup(htmlSource, "html.parser")

            # Get passing advanced stats
            passing_results = soup.find("div", id="all_passing_detailed")
            results = passing_results.find_all(
                "table", class_="stats_table sortable now_sortable")

            for stat_type in results:
                players_not_current = stat_type.find("tbody").find_all("tr")
                for player in players_not_current:
                    try:
                        player_name = player.find("a").text
                        new_name = player_name + str(year)
                        player_stats = player.find_all("td")
                        if new_name not in player_dict:
                            player_dict[new_name] = {}
                        for stat in player_stats:
                            stat_name = stat.get("data-stat")
                            statistic_num = stat.text
                            if statistic_num == "":
                                statistic_num = 0
                            player_dict[new_name][stat_name] = statistic_num
                    except:
                        pass

            # Get rushing advanced stats
            rushing_results = soup.find("div", id="all_advanced_rushing")
            results = rushing_results.find(
                "table", class_="sortable stats_table now_sortable")
            players = results.find("tbody").find_all("tr")

            for player in players:
                try:
                    player_name = player.find("a").text
                    new_name = player_name + str(year)
                    player_stats = player.find_all("td")
                    if new_name not in player_dict:
                        player_dict[new_name] = {}
                    for stat in player_stats:
                        stat_name = stat.get("data-stat")
                        statistic_num = stat.text
                        if statistic_num == "":
                            statistic_num = 0
                        player_dict[new_name][stat_name] = statistic_num
                except:
                    pass

            # Get receiving advanced stats
            receiving_results = soup.find("div", id="all_advanced_receiving")
            results = receiving_results.find(
                "div", id="div_advanced_receiving")
            players = results.find("tbody").find_all("tr")

            for player in players:
                try:
                    player_name = player.find("a").text
                    new_name = player_name + str(year)
                    player_stats = player.find_all("td")
                    if new_name not in player_dict:
                        player_dict[new_name] = {}
                    for stat in player_stats:
                        stat_name = stat.get("data-stat")
                        statistic_num = stat.text
                        if statistic_num == "":
                            statistic_num = 0
                        player_dict[new_name][stat_name] = statistic_num
                except:
                    pass

    with open('nn_data/player_stats.pkl', 'wb') as outp:
        pickle5.dump(player_dict, outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/player_stats.txt', "w") as file:
        for player in player_dict:
            file.write(player + ":\n")
            file.write(str(player_dict[player]) + "\n")


fp_team_abbrev_dict = {'ARI': 'Arizona Cardinals', 'ATL': 'Atlanta Falcons',
                       'BAL': 'Baltimore Ravens', 'BUF': 'Buffalo Bills',
                       'CAR': 'Carolina Panthers', 'CHI': 'Chicago Bears',
                       'CIN': 'Cincinnati Bengals', 'CLE': 'Cleveland Browns',
                       'DAL': 'Dallas Cowboys', 'DEN': 'Denver Broncos',
                       'DET': 'Detroit Lions', 'GB': 'Green Bay Packers',
                       'HOU': 'Houston Texans', 'IND': 'Indianapolis Colts',
                       'JAC': 'Jacksonville Jaguars', 'KC': 'Kansas City Chiefs',
                       'MIA': 'Miami Dolphins', 'MIN': 'Minnesota Vikings',
                       'NE': 'New England Patriots', 'NO': 'New Orleans Saints',
                       'NYG': 'New York Giants', 'NYJ': 'New York Jets',
                       'LV': 'Las Vegas Raiders', 'PHI': 'Philadelphia Eagles',
                       'PIT': 'Pittsburgh Steelers', 'LAC': 'Los Angeles Chargers',
                       'SEA': 'Seattle Seahawks', 'SF': 'San Francisco 49ers',
                       'LAR': 'Los Angeles Rams', 'TB': 'Tampa Bay Buccaneers',
                       'TEN': 'Tennessee Titans', 'WAS': 'Washington Commanders',
                       'BYE': 'Bye Week'}
pfr_team_abbrev_dict = {'buf': 'Buffalo Bills', 'mia': 'Miami Dolphins',
                        'nwe': 'New England Patriots', 'nyj': 'New York Jets',
                        'jax': 'Jacksonville Jaguars', 'oti': 'Tennessee Titans',
                        'clt': 'Indianapolis Colts', 'htx': 'Houston Texans',
                        'cin': 'Cincinnati Bengals', 'rav': 'Baltimore Ravens',
                        'pit': 'Pittsburgh Steelers', 'cle': 'Cleveland Browns',
                        'kan': 'Kansas City Chiefs', 'sdg': 'Los Angeles Chargers',
                        'rai': 'Las Vegas Raiders', 'den': 'Denver Broncos',
                        'phi': 'Philadelphia Eagles', 'dal': 'Dallas Cowboys',
                        'nyg': 'New York Giants', 'was': 'Washington Commanders',
                        'tam': 'Tampa Bay Buccaneers', 'car': 'Carolina Panthers',
                        'nor': 'New Orleans Saints', 'atl': 'Atlanta Falcons',
                        'min': 'Minnesota Vikings', 'det': 'Detroit Lions',
                        'gnb': 'Green Bay Packers', 'chi': 'Chicago Bears',
                        'sfo': 'San Francisco 49ers', 'sea': 'Seattle Seahawks',
                        'ram': 'Los Angeles Rams', 'crd': 'Arizona Cardinals'}

# get_nn_team_data(fp_team_abbrev_dict, pfr_team_abbrev_dict)
get_nn_player_data(fp_team_abbrev_dict, pfr_team_abbrev_dict)
