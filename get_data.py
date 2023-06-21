import time
from selenium import webdriver
from bs4 import BeautifulSoup


def get_data(position, scoring_format_list):
    """
    Get the fantasy football gamelogs for all players in position for the
    2022 NFL season for all of the scoring formats in scoring_format_list
    (i.e. PPR, HALF, STANDARD).
    """
    # URL for position
    position_url = "https://www.fantasypros.com/nfl/stats/" + position + ".php"

    # Chrome webdriver options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    # Different driver paths per computer
    driver_path = "Program Files\Google\Chrome\Application\chrome.exe"
    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    # driver = webdriver.Chrome(options=options)

    # Load the URL in the webdriver
    driver.get(position_url)
    time.sleep(2)

    # Scrolling implementation:
    # Credit: https://medium.com/analytics-vidhya/using-python-and-selenium-to-scrape-infinite-scroll-web-pages-825d12c24ec7
    # scrolling_wait = 1
    # website_height = driver.execute_script(
    #     "return window.screen.height;")
    # i = 1
    # keep_scrolling = True

    # while keep_scrolling:
    #     driver.execute_script(
    #         "window.scrollTo(0, {screen_height}*{i});".format(screen_height=website_height, i=i))
    #     i += 1
    #     time.sleep(scrolling_wait)
    #     scroll_height = driver.execute_script(
    #         "return document.body.scrollHeight;")
    #     if website_height * i > scroll_height:
    #         keep_scrolling = False

    # Parse the HTML content
    htmlSource = driver.page_source
    soup = BeautifulSoup(htmlSource, "html.parser")

    # Extract player prop bets data
    if position == "k" or position == "dst":
        results = soup.find(
            "div", class_="mobile-table").find("tbody")
    else:
        results = soup.find(
            "div", class_="mobile-table double-header").find("tbody")
    player_list = []
    players = results.find_all("tr")

    for player in players:
        player_line = player.find("a", class_="player-name")
        player_link = str(player_line['href'])
        player_name = player_line.text
        player_list.append((player_name, player_link))

    # Write player data to the output file
    for format in scoring_format_list:
        # Open output file
        file_name = "data/" + position + "_" + format + "_output.txt"
        with open(file_name, "a") as file:
            if format == "STANDARD":
                scoring_format = ""
            else:
                scoring_format = "?scoring=" + format
            for player in player_list:
                player_name = player[0]
                ind_player_link = "https://www.fantasypros.com/nfl/games/" + \
                    player[1][11:] + scoring_format
                file.write(player_name + ":\n")
                file.write(ind_player_link + "\n")
                file.write("Games:\n")

                # Get player gamelog
                driver.get(ind_player_link)
                time.sleep(2)

                htmlSource = driver.page_source
                soup = BeautifulSoup(htmlSource, "html.parser")

                # Get games from 2022 season for individual player
                results = soup.find(
                    "div", class_="mobile-table").find("tbody")
                season_games = results.find_all("tr")

                # Get fantasy points for each game
                for game in season_games:
                    stat_list = game.find_all("td")
                    if len(stat_list) > 2:
                        week_stats = (stat_list[0].text, stat_list[-2].text)
                    elif len(stat_list) > 1:
                        week_stats = (stat_list[0].text, stat_list[1].text)
                    else:
                        week_stats = (stat_list[0].text, "")
                    file.write(week_stats[0] + ": " + week_stats[1] + "\n")

                file.write("\n")


# Execute function for all positions and scoring formats
get_data("qb", ["STANDARD"])
get_data("rb", ["PPR", "HALF", "STANDARD"])
get_data("wr", ["PPR", "HALF", "STANDARD"])
get_data("te", ["PPR", "HALF", "STANDARD"])
get_data("k", ["STANDARD"])
get_data("dst", ["STANDARD"])
