import time
from selenium import webdriver
from bs4 import BeautifulSoup
import pickle5
import numpy as np


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
    year = 2018
    team_dict = {}
    for year in range(2018, 2023):
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
                            comma_index = player_pos.find(",")
                            slash_index = player_pos.find("/")
                            if player_pos == "HB":
                                player_pos = "RB"
                            elif comma_index >= 0:
                                player_pos = player_pos[:comma_index]
                            elif slash_index >= 0:
                                player_pos = player_pos[:slash_index]
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

    avg_snap_counts = get_avg_snap_counts(team_dict)

    year = 2023
    # URL for team's schedule
    schedule_url = "https://www.fantasypros.com/nfl/schedule.php?year=2023"
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
        team_dict[team_name] = {}
        team_dict[team_name]["schedule"] = [fp_team_abbrev_dict[opp_team.find(
            "a").text] + str(year) for opp_team in schedule_list]

    for team in fp_team_abbrev_dict:
        if team != "BYE":
            # Get each team's url
            team_name = fp_team_abbrev_dict[team]
            team_url = "https://www.fantasypros.com/nfl/teams/" + \
                team_name.lower().replace(' ', '-') + ".php"
            print(team_url)
            driver.get(team_url)
            time.sleep(2)

            # Parse the HTML content
            htmlSource = driver.page_source
            soup = BeautifulSoup(htmlSource, "html.parser")

            results = soup.find("div", class_="inner")
            positions = results.find_all("div", class_="mobile-table")

            team_dict[team_name + str(year)]["roster"] = []
            for position in positions:
                players = position.find("tbody").find_all("tr")
                player_index = 0
                for player in players:
                    stats = player.find_all("td")
                    position_name = (stats[0].text)[:2]
                    name = stats[1].text
                    snaps = str(
                        avg_snap_counts[team_name][position_name][player_index])
                    if player_index < len(avg_snap_counts[team_name][position_name]) - 1:
                        player_index += 1
                    team_dict[team_name + str(year)]["roster"].append(
                        (name, position_name, snaps, snaps + '%'))

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
    year = 2018
    player_dict = {}
    for year in range(2018, 2023):
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

        indexes = [4, 6, 7, 8, 9, 10, 11, 12]
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


def extract_all_features(player_dict, team_dict, player, position, year, qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight):
    """
    Returns the features.
    """
    previous_year = str(year - 1)
    player_name = player[:-4] + previous_year
    previous_year_player = player_dict[player_name]
    team = player_dict[player]['team']
    team_roster = team_dict[team]['roster']
    used_roster_list = get_roster(
        team_roster, player[:-4], position)
    player_features = []
    for team_player in used_roster_list:
        # team_player_name = team_player[0].split(" ")
        # team_player_name = check_name(team_player_name)
        # new_name = team_player_name[0].title(
        # ) + team_player_name[1].title() + previous_year
        new_name = team_player[0] + previous_year
        team_player_pos = team_player[1]
        if new_name != player_name:
            player_features.append(float(team_player[3][:-1]))
            if team_player_pos == 'QB':
                for feature in qb_keys:
                    try:
                        stat = str(
                            player_dict[new_name][feature])
                        if stat[-1:] == '%':
                            stat = stat[:-1]
                        player_features.append(
                            float(stat.replace(',', '')))
                    except KeyError:
                        try:
                            player_features.append(
                                (avg_weight * qb_avg[previous_year][feature][team[:-4] + previous_year]) + ((1 - avg_weight) * qb_avg[previous_year][feature]['league']))
                        except KeyError:
                            player_features.append(
                                qb_avg[previous_year][feature]['league'])
            elif team_player_pos == 'RB' or team_player_pos == 'FB':
                for feature in rb_keys:
                    try:
                        stat = str(
                            player_dict[new_name][feature])
                        if stat[-1:] == '%':
                            stat = stat[:-1]
                        player_features.append(
                            float(stat.replace(',', '')))
                    except KeyError:
                        try:
                            player_features.append(
                                (avg_weight * rb_avg[previous_year][feature][team[:-4] + previous_year]) + ((1 - avg_weight) * rb_avg[previous_year][feature]['league']))
                        except KeyError:
                            player_features.append(
                                rb_avg[previous_year][feature]['league'])
            elif team_player_pos == 'WR':
                for feature in wr_keys:
                    try:
                        stat = str(
                            player_dict[new_name][feature])
                        if stat[-1:] == '%':
                            stat = stat[:-1]
                        player_features.append(
                            float(stat.replace(',', '')))
                    except KeyError:
                        try:
                            player_features.append(
                                (avg_weight * wr_avg[previous_year][feature][team[:-4] + previous_year]) + ((1 - avg_weight) * wr_avg[previous_year][feature]['league']))
                        except KeyError:
                            player_features.append(
                                wr_avg[previous_year][feature]['league'])
            elif team_player_pos == 'TE':
                for feature in te_keys:
                    try:
                        stat = str(
                            player_dict[new_name][feature])
                        if stat[-1:] == '%':
                            stat = stat[:-1]
                        player_features.append(
                            float(stat.replace(',', '')))
                    except KeyError:
                        try:
                            player_features.append(
                                (avg_weight * te_avg[previous_year][feature][team[:-4] + previous_year]) + ((1 - avg_weight) * te_avg[previous_year][feature]['league']))
                        except KeyError:
                            player_features.append(
                                te_avg[previous_year][feature]['league'])
    if position == 'QB':
        for feature in qb_keys:
            try:
                stat = str(player_dict[player_name][feature])
                if stat[-1:] == '%':
                    stat = stat[:-1]
                player_features.append(
                    float(stat.replace(',', '')))
            except KeyError:
                try:
                    player_features.append(
                        (avg_weight * qb_avg[previous_year][feature][team[:-4] + previous_year]) + ((1 - avg_weight) * qb_avg[previous_year][feature]['league']))
                except KeyError:
                    player_features.append(
                        qb_avg[previous_year][feature]['league'])
        return player_features
    elif position == 'RB':
        for feature in rb_keys:
            try:
                stat = str(player_dict[player_name][feature])
                if stat[-1:] == '%':
                    stat = stat[:-1]
                player_features.append(
                    float(stat.replace(',', '')))
            except KeyError:
                try:
                    player_features.append(
                        (avg_weight * rb_avg[previous_year][feature][team[:-4] + previous_year]) + ((1 - avg_weight) * rb_avg[previous_year][feature]['league']))
                except KeyError:
                    player_features.append(
                        rb_avg[previous_year][feature]['league'])
        return player_features
    elif position == 'WR':
        for feature in wr_keys:
            try:
                stat = str(player_dict[player_name][feature])
                if stat[-1:] == '%':
                    stat = stat[:-1]
                player_features.append(
                    float(stat.replace(',', '')))
            except KeyError:
                try:
                    player_features.append(
                        (avg_weight * wr_avg[previous_year][feature][team[:-4] + previous_year]) + ((1 - avg_weight) * wr_avg[previous_year][feature]['league']))
                except KeyError:
                    player_features.append(
                        wr_avg[previous_year][feature]['league'])
        return player_features
    elif position == 'TE':
        for feature in te_keys:
            try:
                stat = str(player_dict[player_name][feature])
                if stat[-1:] == '%':
                    stat = stat[:-1]
                player_features.append(
                    float(stat.replace(',', '')))
            except KeyError:
                try:
                    player_features.append(
                        (avg_weight * te_avg[previous_year][feature][team[:-4] + previous_year]) + ((1 - avg_weight) * te_avg[previous_year][feature]['league']))
                except KeyError:
                    player_features.append(
                        rb_avg[previous_year][feature]['league'])
        return player_features


def get_test_features(player_dict, team_dict, qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight, player_position):
    """
    Get the features for the players in the 2022 NFL season.
    """
    x_array = []
    player_names = []
    for player in player_dict:
        try:
            position = player_dict[player]['pos']
            year = player[-4:]
            if position == player_position and int(year) == 2022:
                x_array.append(extract_all_features(player_dict, team_dict, player,
                               player_position, 2023, qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight))
                player_names.append(player[:-4])
        except KeyError:
            pass

    return x_array, player_names


def get_features(player_dict, team_dict, qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight, player_position):
    """
    Get the feature data values for the neural network for all players in
    player_dict using team_dict for the team's rosters and qb_keys, rb_keys,
    wr_keys, te_keys as the keys from player_dict to use as features for each
    respective position.

    Fills empty data with the average values from the league in that NFL season
    from that position in qb_avg, rb_avg, wr_avg, te_avg using avg_weight.
    """
    # qb_array = []
    # rb_array = []
    # wr_array = []
    # te_array = []
    x_array = []
    y_array = []
    for test_year in range(2019, 2023):
        for player in player_dict:
            try:
                position = player_dict[player]['pos']
                year = player[-4:]
                if position == player_position and test_year == int(year):
                    # previous_year = str(test_year - 1)
                    # player_name = player[:-4] + previous_year
                    # previous_year_player = player_dict[player_name]
                    fantasy_pts_scored = [
                        float(player_dict[player]['Fantasy Pts'])]
                    x_array.append(extract_all_features(player_dict, team_dict, player,
                                   player_position, test_year, qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight))
                    y_array.append(fantasy_pts_scored)
            except KeyError:
                pass

    return x_array, y_array


def get_avg_values(player_dict, qb_keys, rb_keys, wr_keys, te_keys):
    """
    Get the average values of the keys for each year.
    """
    qb_avg = {'2018': {feature: {'league': (0, 0)} for feature in qb_keys}, '2019': {feature: {'league': (0, 0)} for feature in qb_keys}, '2020': {feature: {'league': (0, 0)} for feature in qb_keys},
              '2021': {feature: {'league': (0, 0)} for feature in qb_keys}, '2022': {feature: {'league': (0, 0)} for feature in qb_keys}}
    rb_avg = {'2018': {feature: {'league': (0, 0)} for feature in rb_keys}, '2019': {feature: {'league': (0, 0)} for feature in rb_keys}, '2020': {feature: {'league': (0, 0)} for feature in rb_keys},
              '2021': {feature: {'league': (0, 0)} for feature in rb_keys}, '2022': {feature: {'league': (0, 0)} for feature in rb_keys}}
    wr_avg = {'2018': {feature: {'league': (0, 0)} for feature in wr_keys}, '2019': {feature: {'league': (0, 0)} for feature in wr_keys}, '2020': {feature: {'league': (0, 0)} for feature in wr_keys},
              '2021': {feature: {'league': (0, 0)} for feature in wr_keys}, '2022': {feature: {'league': (0, 0)} for feature in wr_keys}}
    te_avg = {'2018': {feature: {'league': (0, 0)} for feature in te_keys}, '2019': {feature: {'league': (0, 0)} for feature in te_keys}, '2020': {feature: {'league': (0, 0)} for feature in te_keys},
              '2021': {feature: {'league': (0, 0)} for feature in te_keys}, '2022': {feature: {'league': (0, 0)} for feature in te_keys}}
    for player in player_dict:
        try:
            position = player_dict[player]['pos']
            year = player[-4:]
            team = player_dict[player]['team']
            if position == 'QB':
                for feature in qb_keys:
                    try:
                        stat = str(player_dict[player][feature])
                        if stat[-1:] == '%':
                            stat = stat[:-1]
                        final_stat = float(stat.replace(',', ''))
                        qb_avg[year][feature]['league'] = (
                            qb_avg[year][feature]['league'][0] + final_stat, qb_avg[year][feature]['league'][1] + 1)
                        try:
                            qb_avg[year][feature][team] = (
                                qb_avg[year][feature][team][0] + final_stat, qb_avg[year][feature][team][1] + 1)
                        except KeyError:
                            qb_avg[year][feature][team] = (final_stat, 1)
                    except KeyError:
                        pass
            elif position == 'RB':
                for feature in rb_keys:
                    try:
                        stat = str(player_dict[player][feature])
                        if stat[-1:] == '%':
                            stat = stat[:-1]
                        final_stat = float(stat.replace(',', ''))
                        rb_avg[year][feature]['league'] = (
                            rb_avg[year][feature]['league'][0] + final_stat, rb_avg[year][feature]['league'][1] + 1)
                        try:
                            rb_avg[year][feature][team] = (
                                rb_avg[year][feature][team][0] + final_stat, rb_avg[year][feature][team][1] + 1)
                        except KeyError:
                            rb_avg[year][feature][team] = (final_stat, 1)
                    except KeyError:
                        pass
            elif position == 'WR':
                for feature in wr_keys:
                    try:
                        stat = str(player_dict[player][feature])
                        if stat[-1:] == '%':
                            stat = stat[:-1]
                        final_stat = float(stat.replace(',', ''))
                        wr_avg[year][feature]['league'] = (
                            wr_avg[year][feature]['league'][0] + final_stat, wr_avg[year][feature]['league'][1] + 1)
                        try:
                            wr_avg[year][feature][team] = (
                                wr_avg[year][feature][team][0] + final_stat, wr_avg[year][feature][team][1] + 1)
                        except KeyError:
                            wr_avg[year][feature][team] = (final_stat, 1)
                    except KeyError:
                        pass
            if position == 'TE':
                for feature in te_keys:
                    try:
                        stat = str(player_dict[player][feature])
                        if stat[-1:] == '%':
                            stat = stat[:-1]
                        final_stat = float(stat.replace(',', ''))
                        te_avg[year][feature]['league'] = (
                            te_avg[year][feature]['league'][0] + final_stat, te_avg[year][feature]['league'][1] + 1)
                        try:
                            te_avg[year][feature][team] = (
                                te_avg[year][feature][team][0] + final_stat, te_avg[year][feature][team][1] + 1)
                        except KeyError:
                            te_avg[year][feature][team] = (final_stat, 1)
                    except KeyError:
                        pass
        except KeyError:
            pass
    for year in qb_avg:
        for feature in qb_avg[year]:
            for team in qb_avg[year][feature]:
                try:
                    qb_avg[year][feature][team] = qb_avg[year][feature][team][0] / \
                        qb_avg[year][feature][team][1]
                except:
                    qb_avg[year][feature][team] = qb_avg['2019'][feature][team][0] / \
                        qb_avg['2019'][feature][team][1]
        for feature in rb_avg[year]:
            for team in rb_avg[year][feature]:
                rb_avg[year][feature][team] = rb_avg[year][feature][team][0] / \
                    rb_avg[year][feature][team][1]
        for feature in wr_avg[year]:
            for team in wr_avg[year][feature]:
                wr_avg[year][feature][team] = wr_avg[year][feature][team][0] / \
                    wr_avg[year][feature][team][1]
        for feature in te_avg[year]:
            for team in te_avg[year][feature]:
                te_avg[year][feature][team] = te_avg[year][feature][team][0] / \
                    te_avg[year][feature][team][1]
    return qb_avg, rb_avg, wr_avg, te_avg


def store_features(player_dict, team_dict, qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight):
    """
    Stores the features and values for each position in .txt and .pkl files.
    """
    qb_x, qb_y = get_features(player_dict, team_dict,
                              qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight, "QB")
    rb_x, rb_y = get_features(player_dict, team_dict,
                              qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight, "RB")
    wr_x, wr_y = get_features(player_dict, team_dict,
                              qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight, "WR")
    te_x, te_y = get_features(player_dict, team_dict,
                              qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight, "TE")

    with open('nn_data/qb_features.txt', "w") as file:
        file.write(str(qb_x))
    with open('nn_data/qb_values.txt', "w") as file:
        file.write(str(qb_y))
    with open('nn_data/rb_features.txt', "w") as file:
        file.write(str(rb_x))
    with open('nn_data/rb_values.txt', "w") as file:
        file.write(str(rb_y))
    with open('nn_data/wr_features.txt', "w") as file:
        file.write(str(wr_x))
    with open('nn_data/wr_values.txt', "w") as file:
        file.write(str(wr_y))
    with open('nn_data/te_features.txt', "w") as file:
        file.write(str(te_x))
    with open('nn_data/te_values.txt', "w") as file:
        file.write(str(te_y))

    with open('nn_data/qb_features.pkl', 'wb') as outp:
        pickle5.dump(np.array(qb_x, dtype='float64'),
                     outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/qb_values.pkl', 'wb') as outp:
        pickle5.dump(np.array(qb_y, dtype='float64'),
                     outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/rb_features.pkl', 'wb') as outp:
        pickle5.dump(np.array(rb_x, dtype='float64'),
                     outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/rb_values.pkl', 'wb') as outp:
        pickle5.dump(np.array(rb_y, dtype='float64'),
                     outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/wr_features.pkl', 'wb') as outp:
        pickle5.dump(np.array(wr_x, dtype='float64'),
                     outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/wr_values.pkl', 'wb') as outp:
        pickle5.dump(np.array(wr_y, dtype='float64'),
                     outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/te_features.pkl', 'wb') as outp:
        pickle5.dump(np.array(te_x, dtype='float64'),
                     outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/te_values.pkl', 'wb') as outp:
        pickle5.dump(np.array(te_y, dtype='float64'),
                     outp, pickle5.HIGHEST_PROTOCOL)


def store_test_features(player_dict, team_dict, qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight):
    """
    Stores the test features (2022 NFL season) for each position in .txt and .pkl files.
    """
    qb_x, qb_names = get_test_features(player_dict, team_dict,
                                       qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight, "QB")
    rb_x, rb_names = get_test_features(player_dict, team_dict,
                                       qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight, "RB")
    wr_x, wr_names = get_test_features(player_dict, team_dict,
                                       qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight, "WR")
    te_x, te_names = get_test_features(player_dict, team_dict,
                                       qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, avg_weight, "TE")

    with open('nn_data/qb_test_features.txt', "w") as file:
        file.write(str(qb_x))
    with open('nn_data/rb_test_features.txt', "w") as file:
        file.write(str(rb_x))
    with open('nn_data/wr_test_features.txt', "w") as file:
        file.write(str(wr_x))
    with open('nn_data/te_test_features.txt', "w") as file:
        file.write(str(te_x))

    with open('nn_data/qb_test_features.pkl', 'wb') as outp:
        pickle5.dump(np.array(qb_x, dtype='float64'),
                     outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/rb_test_features.pkl', 'wb') as outp:
        pickle5.dump(np.array(rb_x, dtype='float64'),
                     outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/wr_test_features.pkl', 'wb') as outp:
        pickle5.dump(np.array(wr_x, dtype='float64'),
                     outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/te_test_features.pkl', 'wb') as outp:
        pickle5.dump(np.array(te_x, dtype='float64'),
                     outp, pickle5.HIGHEST_PROTOCOL)

    return qb_names, rb_names, wr_names, te_names


def get_roster(team_roster, player_name, position):
    """
    Get the roster for team in team_dict in year with player_name added as well.
    """
    qb_list = []
    rb_list = []
    wr_list = []
    te_list = []
    qb_limit = 1
    rb_limit = 3
    wr_limit = 5
    te_limit = 3
    if position == "QB":
        qb_list.append((player_name, position, '1000', '100.0%'))
    elif position == "RB":
        rb_list.append((player_name, position, '1000', '100.0%'))
    elif position == "WR":
        wr_list.append((player_name, position, '1000', '100.0%'))
    elif position == "TE":
        te_list.append((player_name, position, '1000', '100.0%'))
    for player in team_roster:
        team_player_name = player[0].split(" ")
        team_player_name = check_name(team_player_name)
        new_name = team_player_name[0].title() + team_player_name[1].title()
        if new_name != player_name:
            position = player[1]
            snap_pct = float(player[3][:-1])
            if position == "QB":
                position_limit = qb_limit
                position_list = qb_list
            elif position == "RB" or position == "FB":
                position_limit = rb_limit
                position_list = rb_list
            elif position == "WR":
                position_limit = wr_limit
                position_list = wr_list
            elif position == "TE":
                position_limit = te_limit
                position_list = te_list
            if len(position_list) < position_limit:
                position_list.append(
                    (new_name, position, player[2], player[3]))
            else:
                min_snap_pct = float('inf')
                replace_index = None
                for i in range(position_limit):
                    i_snap_pct = float(position_list[i][3][:-1])
                    if i_snap_pct < min_snap_pct:
                        min_snap_pct = i_snap_pct
                        replace_index = i
                if snap_pct > min_snap_pct:
                    position_list[replace_index] = (
                        new_name, position, player[2], player[3])

    roster_list = qb_list + rb_list + wr_list + te_list
    # if player_name not in [i[0] for i in roster_list]:
    #    roster_list += [(player_name, None, None, None)]
    return roster_list


def get_avg_snap_counts(team_dict):
    """
    Get the average snap counts for each position on each team from 2018 - 2019.
    """
    avg_snap_counts = {}
    for team in team_dict:
        roster = team_dict[team]['roster']
        team_name = team[:-4]
        year = team[-4:]
        if year == '2018':
            multiplier = 0.2
        elif year == '2019':
            multiplier = 0.4
        elif year == '2020':
            multiplier = 0.6
        elif year == '2021':
            multiplier = 0.8
        elif year == '2022':
            multiplier = 1
        else:
            multiplier = 0
        highest_snaps = 0.0
        for player in roster:
            if player[1] == 'QB':
                if float(player[3][:-1]) > highest_snaps:
                    highest_qb = player[0]
                    highest_snaps = float(player[3][:-1])
        roster_list = get_roster(roster, highest_qb, "QB")
        qb_list = []
        rb_list = []
        wr_list = []
        te_list = []
        for player in roster_list:
            position = player[1]
            if position == "QB":
                position_list = qb_list
            elif position == "RB" or position == "FB":
                position_list = rb_list
            elif position == "WR":
                position_list = wr_list
            elif position == "TE":
                position_list = te_list
            position_list.append(multiplier * float(player[3][:-1]))
        qb_list.sort(reverse=True)
        rb_list.sort(reverse=True)
        wr_list.sort(reverse=True)
        te_list.sort(reverse=True)

        try:
            avg_snap_counts[team_name]['QB'] = [sum(x) for x in zip(
                avg_snap_counts[team_name]['QB'], qb_list)]
            avg_snap_counts[team_name]['RB'] = [sum(x) for x in zip(
                avg_snap_counts[team_name]['RB'], rb_list)]
            avg_snap_counts[team_name]['WR'] = [sum(x) for x in zip(
                avg_snap_counts[team_name]['WR'], wr_list)]
            avg_snap_counts[team_name]['TE'] = [sum(x) for x in zip(
                avg_snap_counts[team_name]['TE'], te_list)]
        except KeyError:
            avg_snap_counts[team_name] = {}
            avg_snap_counts[team_name]['QB'] = qb_list
            avg_snap_counts[team_name]['RB'] = rb_list
            avg_snap_counts[team_name]['WR'] = wr_list
            avg_snap_counts[team_name]['TE'] = te_list

    for team in avg_snap_counts:
        for position in avg_snap_counts[team]:
            avg_snap_counts[team][position] = [snap_count /
                                               3 for snap_count in avg_snap_counts[team][position]]
    return avg_snap_counts


def display_predictions(qb_predictions, rb_predictions, wr_predictions, te_predictions, qb_names, rb_names, wr_names, te_names):
    """
    Store and display the predictions for each position by the neural network.
    """
    qb_dict = {}
    rb_dict = {}
    wr_dict = {}
    te_dict = {}
    assert len(qb_predictions) == len(qb_names)
    assert len(rb_predictions) == len(rb_names)
    assert len(wr_predictions) == len(wr_names)
    assert len(te_predictions) == len(te_names)
    qb_predictions = [x[0] for x in qb_predictions]
    rb_predictions = [x[0] for x in rb_predictions]
    wr_predictions = [x[0] for x in wr_predictions]
    te_predictions = [x[0] for x in te_predictions]
    for index in range(len(qb_predictions)):
        qb_dict[qb_names[index]] = qb_predictions[index]
    for index in range(len(rb_predictions)):
        rb_dict[rb_names[index]] = rb_predictions[index]
    for index in range(len(wr_predictions)):
        wr_dict[wr_names[index]] = wr_predictions[index]
    for index in range(len(te_predictions)):
        te_dict[te_names[index]] = te_predictions[index]
    sorted_qb_dict = dict(
        sorted(qb_dict.items(), key=lambda x: x[1], reverse=True))
    sorted_rb_dict = dict(
        sorted(rb_dict.items(), key=lambda x: x[1], reverse=True))
    sorted_wr_dict = dict(
        sorted(wr_dict.items(), key=lambda x: x[1], reverse=True))
    sorted_te_dict = dict(
        sorted(te_dict.items(), key=lambda x: x[1], reverse=True))

    with open('nn_data/qb_final_predictions.txt', "w") as file:
        for qb in sorted_qb_dict:
            file.write(qb + ": " + str(sorted_qb_dict[qb]) + "\n")
    with open('nn_data/rb_final_predictions.txt', "w") as file:
        for rb in sorted_rb_dict:
            file.write(rb + ": " + str(sorted_rb_dict[rb]) + "\n")
    with open('nn_data/wr_final_predictions.txt', "w") as file:
        for wr in sorted_wr_dict:
            file.write(wr + ": " + str(sorted_wr_dict[wr]) + "\n")
    with open('nn_data/te_final_predictions.txt', "w") as file:
        for te in sorted_te_dict:
            file.write(te + ": " + str(sorted_te_dict[te]) + "\n")


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

qb_keys = ['age', 'g', 'gs', 'pass_cmp', 'pass_att', 'pass_yds', 'pass_target_yds',
           'pass_tgt_yds_per_att', 'pass_air_yds', 'pass_air_yds_per_cmp', 'pass_air_yds_per_att',
           'pass_yac', 'pass_yac_per_cmp', 'pass_batted_passes', 'pass_throwaways',
           'pass_spikes', 'pass_drops', 'pass_drop_pct', 'pass_poor_throws', 'pass_poor_throw_pct',
           'pass_on_target', 'pass_on_target_pct', 'pass_sacked', 'pocket_time', 'pass_blitzed',
           'pass_hurried', 'pass_hits', 'pass_pressured', 'pass_pressured_pct', 'rush_scrambles',
           'rush_scrambles_yds_per_att', 'pass_rpo', 'pass_rpo_yds', 'pass_rpo_pass_att',
           'pass_rpo_pass_yds', 'pass_rpo_rush_att', 'pass_rpo_rush_yds', 'pass_play_action',
           'pass_play_action_pass_yds', 'rush_att', 'rush_yds', 'rush_td', 'rush_first_down',
           'rush_yds_before_contact', 'rush_yds_bc_per_rush', 'rush_yac', 'rush_yac_per_rush',
           'rush_broken_tackles', 'rush_broken_tackles_per_rush', 'Snaps', 'Snap %', 'Rush %',
           'Tgt %', 'Touch %', 'Util %', '10+ YDS', '20+ YDS', '30+ YDS', '40+ YDS', '50+ YDS',
           'RTG', 'redzone completions', 'redzone attempts', 'redzone completion %',
           'redzone passing yards', 'redzone passing y/a', 'redzone passing TDs',
           'redzone interceptions', 'redzone sacks', 'redzone rushing attempts',
           'redzone rushing yards', 'redzone rushing TDs']
rb_keys = ['age', 'g', 'gs', 'rush_att', 'rush_yds', 'rush_td', 'rush_first_down',
           'rush_yds_before_contact', 'rush_yds_bc_per_rush', 'rush_yac', 'rush_yac_per_rush',
           'rush_broken_tackles', 'rush_broken_tackles_per_rush', 'targets', 'rec', 'rec_yds',
           'rec_td', 'rec_first_down', 'rec_air_yds', 'rec_air_yds_per_rec', 'rec_yac',
           'rec_yac_per_rec', 'rec_adot', 'rec_broken_tackles', 'rec_broken_tackles_per_rec',
           'rec_drops', 'rec_drop_pct', 'rec_target_int', 'rec_pass_rating', 'Snaps', 'Snap %',
           'Rush %', 'Tgt %', 'Touch %', 'Util %', 'TK LOSS', 'TK LOSS YDS', 'LNG TD', '10+ YDS',
           '20+ YDS', '30+ YDS', '40+ YDS', '50+ YDS', 'LNG', 'redzone rushing attempts',
           'redzone rushing yards', 'redzone rushing y/a', 'redzone rushing TDs', 'redzone rushing %',
           'redzone receptions', 'redzone targets', 'redzone receiving %', 'redzone receiving yards',
           'redzone receiving y/r', 'redzone receiving TDs', 'redzone target %']
wr_keys = ['age', 'g', 'gs', 'rush_att', 'rush_yds', 'rush_td', 'rush_first_down',
           'rush_yds_before_contact', 'rush_yds_bc_per_rush', 'rush_yac', 'rush_yac_per_rush',
           'rush_broken_tackles', 'rush_broken_tackles_per_rush', 'targets', 'rec',
           'rec_yds', 'rec_td', 'rec_first_down', 'rec_air_yds', 'rec_air_yds_per_rec',
           'rec_yac', 'rec_yac_per_rec', 'rec_adot', 'rec_broken_tackles', 'rec_broken_tackles_per_rec',
           'rec_drops', 'rec_drop_pct', 'rec_target_int', 'rec_pass_rating', 'Snaps',
           'Snap %', 'Rush %', 'Tgt %', 'Touch %', 'Util %', 'CATCHABLE', '10+ YDS', '20+ YDS',
           '30+ YDS', '40+ YDS', '50+ YDS', 'LNG', 'redzone receptions', 'redzone targets',
           'redzone receiving %', 'redzone receiving yards', 'redzone receiving y/r',
           'redzone receiving TDs', 'redzone target %', 'redzone rushing attempts',
           'redzone rushing yards', 'redzone rushing TDs', 'redzone rushing %']
te_keys = ['age', 'g', 'gs', 'rush_att', 'rush_yds', 'rush_td', 'rush_first_down',
           'rush_yds_before_contact', 'rush_yds_bc_per_rush', 'rush_yac', 'rush_yac_per_rush',
           'rush_broken_tackles', 'rush_broken_tackles_per_rush', 'targets', 'rec', 'rec_yds',
           'rec_td', 'rec_first_down', 'rec_air_yds', 'rec_air_yds_per_rec', 'rec_yac',
           'rec_yac_per_rec', 'rec_adot', 'rec_broken_tackles', 'rec_broken_tackles_per_rec',
           'rec_drops', 'rec_drop_pct', 'rec_target_int', 'rec_pass_rating', 'Snaps',
           'Snap %', 'Rush %', 'Tgt %', 'Touch %', 'Util %', 'CATCHABLE', '10+ YDS', '20+ YDS',
           '30+ YDS', '40+ YDS', '50+ YDS', 'LNG', 'redzone receptions', 'redzone targets',
           'redzone receiving %', 'redzone receiving yards', 'redzone receiving y/r',
           'redzone receiving TDs', 'redzone target %', 'redzone rushing attempts',
           'redzone rushing yards', 'redzone rushing TDs', 'redzone rushing %']

# get_nn_team_data(fp_team_abbrev_dict, pfr_team_abbrev_dict)
# get_nn_player_data(fp_team_abbrev_dict, pfr_team_abbrev_dict)

player_dict = {}
with open('nn_data/player_stats.pkl', 'rb') as inp:
    player_dict = pickle5.load(inp)
team_dict = {}
with open('nn_data/team_stats.pkl', 'rb') as inp:
    team_dict = pickle5.load(inp)

qb_avg, rb_avg, wr_avg, te_avg = get_avg_values(
    player_dict, qb_keys, rb_keys, wr_keys, te_keys)
# with open('nn_data/average_position_data.txt', 'w') as file:
#     file.write(str(qb_avg))
#     file.write("\n")
#     file.write(str(rb_avg))
#     file.write("\n")
#     file.write(str(wr_avg))
#     file.write("\n")
#     file.write(str(te_avg))

# get_player_gamelogs(player_dict, fp_team_abbrev_dict)
# store_features(player_dict, team_dict, qb_keys, rb_keys,
#                wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, 0)
qb_names, rb_names, wr_names, te_names = store_test_features(
    player_dict, team_dict, qb_keys, rb_keys, wr_keys, te_keys, qb_avg, rb_avg, wr_avg, te_avg, 0)

with open('nn_data/qb_predictions.pkl', 'rb') as inp:
    qb_predictions = pickle5.load(inp)
with open('nn_data/rb_predictions.pkl', 'rb') as inp:
    rb_predictions = pickle5.load(inp)
with open('nn_data/wr_predictions.pkl', 'rb') as inp:
    wr_predictions = pickle5.load(inp)
with open('nn_data/te_predictions.pkl', 'rb') as inp:
    te_predictions = pickle5.load(inp)
display_predictions(qb_predictions, rb_predictions, wr_predictions,
                    te_predictions, qb_names, rb_names, wr_names, te_names)
