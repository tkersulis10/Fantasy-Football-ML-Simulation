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
                        player_name = (player.find("a").text).split(" ")
                        player_name = check_name(player_name)
                        new_name = player_name[0].title(
                        ) + player_name[1].title() + str(year)
                        player_stats = player.find_all("td")
                        if new_name not in player_dict:
                            player_dict[new_name] = {}
                            player_dict[new_name]["team"] = pfr_team_abbrev_dict[team] + \
                                str(year)
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
                    player_name = (player.find("a").text).split(" ")
                    player_name = check_name(player_name)
                    new_name = player_name[0].title(
                    ) + player_name[1].title() + str(year)
                    player_stats = player.find_all("td")
                    if new_name not in player_dict:
                        player_dict[new_name] = {}
                        player_dict[new_name]["team"] = pfr_team_abbrev_dict[team] + \
                            str(year)
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
                    player_name = (player.find("a").text).split(" ")
                    player_name = check_name(player_name)
                    new_name = player_name[0].title(
                    ) + player_name[1].title() + str(year)
                    player_stats = player.find_all("td")
                    if new_name not in player_dict:
                        player_dict[new_name] = {}
                        player_dict[new_name]["team"] = pfr_team_abbrev_dict[team] + \
                            str(year)
                    for stat in player_stats:
                        stat_name = stat.get("data-stat")
                        statistic_num = stat.text
                        if statistic_num == "":
                            statistic_num = 0
                        player_dict[new_name][stat_name] = statistic_num
                except:
                    pass

        # URL for snap counts
        player_snap_url = "https://www.fantasypros.com/nfl/reports/snap-count-analysis/?year=" + \
            str(year) + "&scoring=HALF&snaps=10"
        driver.get(player_snap_url)
        time.sleep(2)

        # Parse the HTML content
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource, "html.parser")

        # Get snap stats
        results = soup.find("div", class_="mobile-table")
        results_header = results.find("thead")
        results_players = results.find("tbody")
        headers = results_header.find_all("th")
        players = results_players.find_all("tr")

        indexes = [4, 6, 7, 8, 9, 10, 12]
        stat_names = []
        for header in headers:
            stat_names.append(header.text)
        stat_names = [stat_names[i] for i in indexes]
        for player in players:
            player_name = (player.find("a").text).split(" ")
            player_name = check_name(player_name)
            new_name = player_name[0].title(
            ) + player_name[1].title() + str(year)
            if new_name not in player_dict:
                player_dict[new_name] = {}
            stat_list = player.find_all("td")
            stat_count = 0
            index_count = 0
            for stat in stat_list:
                if stat_count == indexes[index_count]:
                    player_dict[new_name][stat_names[index_count]] = stat.text
                    index_count += 1
                stat_count += 1

        # URL for target gamelog
        player_target_log_url = "https://www.fantasypros.com/nfl/reports/targets/?year=" + \
            str(year) + "&start=1&end=18"
        driver.get(player_target_log_url)
        time.sleep(2)

        # Parse the HTML content
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource, "html.parser")

        # Get target stats
        results = soup.find("div", class_="mobile-table").find("tbody")
        players = results.find_all("tr")

        for player in players:
            player_name = (player.find("a").text).split(" ")
            player_name = check_name(player_name)
            new_name = player_name[0].title(
            ) + player_name[1].title() + str(year)
            if new_name not in player_dict:
                player_dict[new_name] = {}
            stat_list = player.find_all("td")
            target_gamelog = []
            for stat in stat_list[3:-2]:
                target_gamelog.append(stat.text)
            player_dict[new_name]["target gamelog"] = target_gamelog

        # URL for fantasypros wr advanced stats
        wr_adv_url = "https://www.fantasypros.com/nfl/advanced-stats-wr.php?year=" + \
            str(year)
        driver.get(wr_adv_url)
        time.sleep(2)

        # Parse the HTML content
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource, "html.parser")

        # Get fantasypros wr advanced stats
        results = soup.find("div", class_="mobile-table double-header")
        results_header = results.find("thead").find(
            "tr", class_="tablesorter-header")
        results_players = results.find("tbody")
        headers = results_header.find_all("th")
        players = results_players.find_all("tr")

        indexes = [17, 20, 21, 22, 23, 24, 25]
        stat_names = []
        for header in headers:
            stat_names.append(header.text)
        stat_names = [stat_names[i] for i in indexes]
        for player in players:
            player_name = (player.find("a").text).split(" ")
            player_name = check_name(player_name)
            new_name = player_name[0].title(
            ) + player_name[1].title() + str(year)
            if new_name not in player_dict:
                player_dict[new_name] = {}
            stat_list = player.find_all("td")
            stat_count = 0
            index_count = 0
            for stat in stat_list:
                if stat_count == indexes[index_count]:
                    player_dict[new_name][stat_names[index_count]] = stat.text
                    index_count += 1
                stat_count += 1
            player_dict[new_name]["fp link"] = stat_list[1].find(
                "a").get("href")

        # URL for fantasypros te advanced stats
        te_adv_url = "https://www.fantasypros.com/nfl/advanced-stats-te.php?year=" + \
            str(year)
        driver.get(te_adv_url)
        time.sleep(2)

        # Parse the HTML content
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource, "html.parser")

        # Get fantasypros te advanced stats
        results = soup.find("div", class_="mobile-table double-header")
        results_header = results.find("thead").find(
            "tr", class_="tablesorter-header")
        results_players = results.find("tbody")
        headers = results_header.find_all("th")
        players = results_players.find_all("tr")

        indexes = [17, 20, 21, 22, 23, 24, 25]
        stat_names = []
        for header in headers:
            stat_names.append(header.text)
        stat_names = [stat_names[i] for i in indexes]
        for player in players:
            player_name = (player.find("a").text).split(" ")
            player_name = check_name(player_name)
            new_name = player_name[0].title(
            ) + player_name[1].title() + str(year)
            if new_name not in player_dict:
                player_dict[new_name] = {}
            stat_list = player.find_all("td")
            stat_count = 0
            index_count = 0
            for stat in stat_list:
                if stat_count == indexes[index_count]:
                    player_dict[new_name][stat_names[index_count]] = stat.text
                    index_count += 1
                stat_count += 1
            player_dict[new_name]["fp link"] = stat_list[1].find(
                "a").get("href")

        # URL for fantasypros rb advanced stats
        rb_adv_url = "https://www.fantasypros.com/nfl/advanced-stats-rb.php?year=" + \
            str(year)
        driver.get(rb_adv_url)
        time.sleep(2)

        # Parse the HTML content
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource, "html.parser")

        # Get fantasypros rb advanced stats
        results = soup.find("div", class_="mobile-table double-header")
        results_header = results.find("thead").find(
            "tr", class_="tablesorter-header")
        results_players = results.find("tbody")
        headers = results_header.find_all("th")
        players = results_players.find_all("tr")

        indexes = [11, 12, 13, 14, 15, 16, 17, 18, 19]
        stat_names = []
        for header in headers:
            stat_names.append(header.text)
        stat_names = [stat_names[i] for i in indexes]
        for player in players:
            player_name = (player.find("a").text).split(" ")
            player_name = check_name(player_name)
            new_name = player_name[0].title(
            ) + player_name[1].title() + str(year)
            if new_name not in player_dict:
                player_dict[new_name] = {}
            stat_list = player.find_all("td")
            stat_count = 0
            index_count = 0
            for stat in stat_list:
                try:
                    if stat_count == indexes[index_count]:
                        player_dict[new_name][stat_names[index_count]
                                              ] = stat.text
                        index_count += 1
                except:
                    pass
                stat_count += 1
            player_dict[new_name]["fp link"] = stat_list[1].find(
                "a").get("href")

        # URL for fantasypros qb advanced stats
        qb_adv_url = "https://www.fantasypros.com/nfl/advanced-stats-qb.php?year=" + \
            str(year)
        driver.get(qb_adv_url)
        time.sleep(2)

        # Parse the HTML content
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource, "html.parser")

        # Get fantasypros qb advanced stats
        results = soup.find("div", class_="mobile-table double-header")
        results_header = results.find("thead").find(
            "tr", class_="tablesorter-header")
        results_players = results.find("tbody")
        headers = results_header.find_all("th")
        players = results_players.find_all("tr")

        indexes = [10, 11, 12, 13, 14, 23]
        stat_names = []
        for header in headers:
            stat_names.append(header.text)
        stat_names = [stat_names[i] for i in indexes]
        for player in players:
            player_name = (player.find("a").text).split(" ")
            player_name = check_name(player_name)
            new_name = player_name[0].title(
            ) + player_name[1].title() + str(year)
            if new_name not in player_dict:
                player_dict[new_name] = {}
            stat_list = player.find_all("td")
            stat_count = 0
            index_count = 0
            for stat in stat_list:
                if stat_count == indexes[index_count]:
                    player_dict[new_name][stat_names[index_count]] = stat.text
                    index_count += 1
                stat_count += 1
            player_dict[new_name]["fp link"] = stat_list[1].find(
                "a").get("href")

        # URL for qb redzone stats
        qb_redzone_url = "https://www.fantasypros.com/nfl/red-zone-stats/qb.php?year=" + \
            str(year) + "&range=full&scoring=HALF"
        driver.get(qb_redzone_url)
        time.sleep(2)

        # Parse the HTML content
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource, "html.parser")

        # Get qb redzone stats
        results = soup.find("div", class_="mobile-table double-header")
        results_players = results.find("tbody")
        players = results_players.find_all("tr")

        stat_names = ["redzone completions", "redzone attempts", "redzone completion %",
                      "redzone passing yards", "redzone passing y/a", "redzone passing TDs",
                      "redzone interceptions", "redzone sacks", "redzone rushing attempts",
                      "redzone rushing yards", "redzone rushing TDs", "redzone fpts"]
        for player in players:
            player_name = (player.find("a").text).split(" ")
            player_name = check_name(player_name)
            new_name = player_name[0].title(
            ) + player_name[1].title() + str(year)
            if new_name not in player_dict:
                player_dict[new_name] = {}
            stat_list = player.find_all("td")
            stat_count = 0
            for stat in stat_list[2:13]:
                player_dict[new_name][stat_names[stat_count]] = stat.text
                stat_count += 1
            player_dict[new_name][stat_names[stat_count]] = stat_list[16].text

        # URL for rb redzone stats
        rb_redzone_url = "https://www.fantasypros.com/nfl/red-zone-stats/rb.php?year=" + \
            str(year) + "&range=full&scoring=HALF"
        driver.get(rb_redzone_url)
        time.sleep(2)

        # Parse the HTML content
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource, "html.parser")

        # Get rb redzone stats
        results = soup.find("div", class_="mobile-table double-header")
        results_players = results.find("tbody")
        players = results_players.find_all("tr")

        stat_names = ["redzone rushing attempts", "redzone rushing yards", "redzone rushing y/a",
                      "redzone rushing TDs", "redzone rushing %", "redzone receptions",
                      "redzone targets", "redzone receiving %", "redzone receiving yards",
                      "redzone receiving y/r", "redzone receiving TDs", "redzone target %",
                      "redzone fpts"]
        for player in players:
            player_name = (player.find("a").text).split(" ")
            player_name = check_name(player_name)
            new_name = player_name[0].title(
            ) + player_name[1].title() + str(year)
            if new_name not in player_dict:
                player_dict[new_name] = {}
            stat_list = player.find_all("td")
            stat_count = 0
            for stat in stat_list[2:14]:
                player_dict[new_name][stat_names[stat_count]] = stat.text
                stat_count += 1
            player_dict[new_name][stat_names[stat_count]] = stat_list[16].text

        # URL for wr redzone stats
        wr_redzone_url = "https://www.fantasypros.com/nfl/red-zone-stats/wr.php?year=" + \
            str(year) + "&range=full&scoring=HALF"
        driver.get(wr_redzone_url)
        time.sleep(2)

        # Parse the HTML content
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource, "html.parser")

        # Get wr redzone stats
        results = soup.find("div", class_="mobile-table double-header")
        results_players = results.find("tbody")
        players = results_players.find_all("tr")

        stat_names = ["redzone receptions", "redzone targets", "redzone receiving %",
                      "redzone receiving yards", "redzone receiving y/r", "redzone receiving TDs",
                      "redzone target %", "redzone rushing attempts", "redzone rushing yards",
                      "redzone rushing TDs", "redzone rushing %", "redzone fpts"]
        for player in players:
            player_name = (player.find("a").text).split(" ")
            player_name = check_name(player_name)
            new_name = player_name[0].title(
            ) + player_name[1].title() + str(year)
            if new_name not in player_dict:
                player_dict[new_name] = {}
            stat_list = player.find_all("td")
            stat_count = 0
            for stat in stat_list[2:13]:
                player_dict[new_name][stat_names[stat_count]] = stat.text
                stat_count += 1
            player_dict[new_name][stat_names[stat_count]] = stat_list[15].text

        # URL for te redzone stats
        te_redzone_url = "https://www.fantasypros.com/nfl/red-zone-stats/te.php?year=" + \
            str(year) + "&range=full&scoring=HALF"
        driver.get(te_redzone_url)
        time.sleep(2)

        # Parse the HTML content
        htmlSource = driver.page_source
        soup = BeautifulSoup(htmlSource, "html.parser")

        # Get te redzone stats
        results = soup.find("div", class_="mobile-table double-header")
        results_players = results.find("tbody")
        players = results_players.find_all("tr")

        stat_names = ["redzone receptions", "redzone targets", "redzone receiving %",
                      "redzone receiving yards", "redzone receiving y/r", "redzone receiving TDs",
                      "redzone target %", "redzone rushing attempts", "redzone rushing yards",
                      "redzone rushing TDs", "redzone rushing %", "redzone fpts"]
        for player in players:
            player_name = (player.find("a").text).split(" ")
            player_name = check_name(player_name)
            new_name = player_name[0].title(
            ) + player_name[1].title() + str(year)
            if new_name not in player_dict:
                player_dict[new_name] = {}
            stat_list = player.find_all("td")
            stat_count = 0
            for stat in stat_list[2:13]:
                player_dict[new_name][stat_names[stat_count]] = stat.text
                stat_count += 1
            player_dict[new_name][stat_names[stat_count]] = stat_list[15].text

    with open('nn_data/player_stats.pkl', 'wb') as outp:
        pickle5.dump(player_dict, outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/player_stats.txt', "w") as file:
        for player in player_dict:
            file.write(player + ":\n")
            file.write(str(player_dict[player]) + "\n")


def get_player_gamelogs(player_dict, fp_team_abbrev_dict):
    """
    Get the fantasy gamelogs and add them to player_dict for all the players
    with gamelogs on fantasypros in player_dict. The opponents are converted
    to full names using fp_team_abbrev_dict
    """
    # Chrome webdriver options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    # Different driver paths per computer
    driver_path = "Program Files\Google\Chrome\Application\chrome.exe"
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    # driver = webdriver.Chrome(options=options)

    player_gamelog_dict = {}
    for player in player_dict:
        try:
            # Get player's fantasy gamelog url
            year = player[-4:]
            link = player_dict[player]["fp link"][11:]
            gamelog_url = "https://www.fantasypros.com/nfl/games/" + \
                link + "?season=" + year + "&scoring=HALF"
            driver.get(gamelog_url)
            time.sleep(2)

            # Parse the HTML content
            htmlSource = driver.page_source
            soup = BeautifulSoup(htmlSource, "html.parser")

            # Get player fantasy gamelog
            results = soup.find("div", class_="mobile-table")
            results_header = results.find("thead").find_all("tr")
            top_header = results_header[0].find_all("th")
            bottom_header = results_header[1].find_all("th")
            results_games = results.find("tbody")
            games = results_games.find_all("tr")

            top_header_spans = [int(th.get("colspan")) for th in top_header]
            top_header_labels = [th.text for th in top_header]
            bottom_header_labels = [th.text for th in bottom_header]
            player_gamelog = []
            for game in games:
                game_dict = {}
                top_header_count = 1
                top_header_index = 0
                bottom_header_index = 1
                stat_list = game.find_all("td")[1:]
                if len(stat_list) < 3:
                    game_dict = {"Game OPP": "BYE Week"}
                else:
                    opponent = fp_team_abbrev_dict[stat_list[0].text.split(" ")[
                        1]] + year
                    stat_name = top_header_labels[top_header_index] + \
                        " " + bottom_header_labels[bottom_header_index]
                    game_dict[stat_name] = opponent
                    top_header_count += 1
                    bottom_header_index += 1
                    if top_header_count >= top_header_spans[top_header_index]:
                        top_header_count = 0
                        top_header_index += 1
                    for stat in stat_list[1:]:
                        stat_name = top_header_labels[top_header_index] + \
                            " " + bottom_header_labels[bottom_header_index]
                        stat_num = stat.text
                        game_dict[stat_name] = stat_num
                        top_header_count += 1
                        bottom_header_index += 1
                        if top_header_count >= top_header_spans[top_header_index]:
                            top_header_count = 0
                            top_header_index += 1
                player_gamelog.append(game_dict)
            player_gamelog_dict[player] = player_gamelog
        except:
            pass

    with open('nn_data/player_gamelogs.pkl', 'wb') as outp:
        pickle5.dump(player_gamelog_dict, outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/player_gamelogs.txt', "w") as file:
        for player in player_gamelog_dict:
            file.write(player + ":\n")
            file.write(str(player_gamelog_dict[player]) + "\n")


def check_name(player_name):
    """
    Checks for discrepancies in player_name from fantasypros to
    pro football reference.
    """
    first_name = player_name[0].title()
    last_name = player_name[1].title()
    if first_name == "Mitch" and last_name == "Trubisky":
        return ["Mitchell", "Trubisky"]
    elif first_name == "Dk" and last_name == "Metcalf":
        return ["D.K.", "Metcalf"]
    elif first_name == "Dj" and last_name == "Moore":
        return ["D.J.", "Moore"]
    elif first_name == "Gabe" and last_name == "Davis":
        return ["Gabriel", "Davis"]
    elif first_name == "Joshua" and last_name == "Palmer":
        return ["Josh", "Palmer"]
    elif first_name == "Amon-Ra" and last_name == "St.":
        return ["Amon-Ra", "St.Brown"]
    elif first_name == "Equanimeous" and last_name == "St.":
        return ["Equanimeous", "St.Brown"]
    else:
        return player_name


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

# player_dict = {}
# with open('nn_data/player_stats.pkl', 'rb') as inp:
#     player_dict = pickle5.load(inp)
# get_player_gamelogs(player_dict, fp_team_abbrev_dict)
