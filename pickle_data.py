import os
import pickle5


class Position:
    """
    Each position represents all of the players from the 2022 NFL season with
    a specific position and scoring format. The players are represented by a
    list of weekly fantasy scores for that season in this specific scoring
    format.
    """

    def __init__(self, position, format):
        self.position = position
        self.format = format
        self.players = {}

    def __repr__(self):
        return str(self.__dict__)

    def pickle_data_file(self):
        """
        Turn the raw data from the .txt file associated with self.position and
        self.format into a pickled file.
        """
        # Get the file associated with this position and scoring format
        file_name = "data/" + self.position + "_" + self.format + "_output.txt"
        with open(file_name) as file:
            # Read the file
            lines = file.readlines()

            # Get first plater in the file
            current_player = lines[0][:-2]
            current_gamelog = []
            next_line_player = False

            # Limit number of players for each position
            num_players = 0
            if self.position == "qb":
                player_limit = 50
            elif self.position == "rb":
                player_limit = 70
            elif self.position == "wr":
                player_limit = 100
            elif self.position == "te":
                player_limit = 50
            else:
                player_limit = 50

            # Iterate over all file lines
            for line in lines[1:]:
                if num_players < player_limit:
                    # Check if the line is a player's name
                    if next_line_player:
                        current_player = line[:-2]
                        next_line_player = False
                        current_gamelog = []

                    # Check if the line is the end of a player's gamelog
                    elif line == "\n":
                        self.players[current_player] = current_gamelog
                        next_line_player = True
                        num_players += 1

                    # Check if the line is a player's game
                    elif line[:4] == "Week":
                        try:
                            current_gamelog.append(float(line[8:-1].strip()))
                        except:
                            current_gamelog.append(line[8:-1].strip())


# Iterate over all .txt files in the data directory
for file in os.listdir("./data"):
    if file.endswith(".txt"):
        # Get the file name and the position and scoring format of the file
        file_name = os.path.join("data", file)

        first_underscore = file_name.find("_")
        second_underscore = file_name.find("_", first_underscore + 1)

        position = file_name[5:first_underscore]
        format = file_name[first_underscore + 1: second_underscore]

        # Pickle the data and dump it into a new file
        player_dict = Position(position, format)
        player_dict.pickle_data_file()
        pickle_file_name = "data\\" + position + "_" + format + ".pkl"
        with open(pickle_file_name, 'wb') as outp:
            pickle5.dump(player_dict.players, outp, pickle5.HIGHEST_PROTOCOL)

# Example Usage:
# players_dict = {}
# with open('data/qb_STANDARD.pkl', 'rb') as inp:
#     players_dict = pickle5.load(inp)
# print(players_dict['Dak Prescott'])

# players_dict = {}
# with open('data/rb_HALF.pkl', 'rb') as inp:
#     players_dict = pickle5.load(inp)
# print(players_dict['Travis Etienne Jr.'])
