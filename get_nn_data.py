import time
from selenium import webdriver
from bs4 import BeautifulSoup
import pickle5


def get_nn_data(team_abbrev_dict):
    """
    Get the fantasy football advanced data for players. team_abbrev_dict is a
    dictionary where the keys are each team's abbreviation (i.e. SF) and the
    values are each team's full name (i.e. San Francisco 49ers)
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
            team_dict[team_name] = [[stat.text for stat in stat_list]]

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
                team_dict[team_name].append(
                    [stat_list[i].text for i in range(1, len(stat_list), 2)])
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
            team_dict[team_name].append([team_abbrev_dict[opp_team.find(
                "a").text] + str(year) for opp_team in schedule_list])

    with open('nn_data/team_stats.pkl', 'wb') as outp:
        pickle5.dump(team_dict, outp, pickle5.HIGHEST_PROTOCOL)
    with open('nn_data/team_stats.txt', "a") as file:
        for team in team_dict:
            file.write(team + ":\n")
            file.write(str(team_dict[team]) + "\n")


team_abbrev_dict = {'ARI': 'Arizona Cardinals', 'ATL': 'Atlanta Falcons',
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
get_nn_data(team_abbrev_dict)
