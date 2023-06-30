import random
import pickle5
import numpy as np
import simulate2
import copy


class Tuple:
    def __init__(self, player_name, player_gamelog):
        self.player_name = player_name
        self.player_gamelog = player_gamelog

    def __hash__(self):
        return hash(self.player_name)

    def __eq__(self, other):
        return self.player_name == other.player_name

    def __repr__(self):
        return self.player_name

    def __str__(self):
        return self.player_name

    def get_gamelog(self):
        return self.player_gamelog


class Draft:
    """
    Represents the fantasy football draft. The Draft keeps track of what the
    current pick and round is, the total number of rounds, and whether the
    draft has ended of not.
    """

    def __init__(self, num_teams, roster, num_rounds, scoring_format, num_training):
        """
        Initializes the draft to the start (first pick of the draft) with
        num_teams (# of teams in the draft), num_rounds (# of rounds in the
        draft), scoring format (i.e. "STANDARD", "HALF", or "PPR"), and
        num_training total number of training steps.

        Roster is a dictionary where the keys are positions (i.e. "qb", "rb",
        etc.) and the values are a list of the players on that team's roster
        for that position (which is initially empty).
        """
        self.num_teams = num_teams
        self.current_pick = 0
        self.current_round = 1
        self.num_rounds = num_rounds
        self.end_draft = False
        self.scoring_format = scoring_format
        self.initial_players = self.get_initial_players()
        self.available_players = copy.deepcopy(self.initial_players)
        self.empty_rosters = [copy.deepcopy(roster) for i in range(num_teams)]
        self.rosters = copy.deepcopy(self.empty_rosters)
        self.drafters = [ValueIterationDrafter(i, 0.5, 0.5)
                         for i in range(num_teams)]
        self.num_training = num_training

    def get_initial_players(self):
        """
        Returns a dictionary of all of the available players to be drafted
        to start.

        The dictionary has a key for each position and the values are another
        dictionary from player names to their gamelogs for each player in
        that position.
        """
        players_dict = {}
        with open('data/qb_STANDARD.pkl', 'rb') as inp:
            players_dict["qb"] = self.convert_gamelog(pickle5.load(inp))
        with open('data/rb_' + self.scoring_format + '.pkl', 'rb') as inp:
            players_dict["rb"] = self.convert_gamelog(pickle5.load(inp))
        with open('data/wr_' + self.scoring_format + '.pkl', 'rb') as inp:
            players_dict["wr"] = self.convert_gamelog(pickle5.load(inp))
        with open('data/te_' + self.scoring_format + '.pkl', 'rb') as inp:
            players_dict["te"] = self.convert_gamelog(pickle5.load(inp))
        with open('data/dst_STANDARD.pkl', 'rb') as inp:
            players_dict["dst"] = self.convert_gamelog(pickle5.load(inp))
        with open('data/k_STANDARD.pkl', 'rb') as inp:
            players_dict["k"] = self.convert_gamelog(pickle5.load(inp))
        return players_dict

    def convert_gamelog(self, players_dict):
        """
        Returns a converted dictionary where the values of players_dict are
        converted from a list of a mix of floats and strings to a numpy array
        of only floats.

        Deletes the players with no games in the NFL season.
        """
        new_dict = {}
        for player in players_dict:
            gamelog_list = players_dict[player]
            number_games = len(gamelog_list)
            if number_games > 0:
                if number_games < 17:
                    gamelog_list += [0.0] * (17 - number_games)
                new_dict[player] = np.array(
                    [0.0 if type(i) != float else i for i in gamelog_list])
        return new_dict

    def get_available_players(self):
        """
        Returns the available players to be drafted.
        """
        all_positions_list = []
        for position in self.available_players:
            for player_name in self.available_players[position]:
                all_positions_list.append((player_name, position))
        return all_positions_list

    def pick_player(self, player_name, player_position):
        """
        Simulates drafting a player from the available players. Also checks
        and sets self.end_draft to true if this is the end of the draft.
        """
        player_pick = self.available_players[player_position].pop(player_name)
        # self.rosters[self.current_pick][player_position].add(player_pick)
        self.rosters[self.current_pick][player_position].add(
            Tuple(player_name, player_pick))
        if self.current_round % 2 == 1:
            if self.current_pick < self.num_teams - 1:
                self.current_pick += 1
            else:
                self.current_round += 1
                if self.current_round > self.num_rounds:
                    self.end_draft = True
        else:
            if self.current_pick > 0:
                self.current_pick -= 1
            else:
                self.current_round += 1
                if self.current_round > self.num_rounds:
                    self.end_draft = True

    def get_end_draft(self):
        """
        Returns whether the draft has ended or not.
        """
        return self.end_draft

    def run_draft(self):
        """
        Runs the draft going pick by pick through the draft and does this for
        self.num_training total number of steps.
        """
        draft_number = 1
        print("Draft " + str(draft_number))
        for training_episode in range(self.num_training):
            if self.get_end_draft():
                self.current_pick = 0
                self.current_round = 1
                self.end_draft = False
                self.available_players = copy.deepcopy(self.initial_players)
                self.rosters = copy.deepcopy(self.empty_rosters)
                draft_number += 1
                print("Draft " + str(draft_number))
            current_state = State(self.rosters[self.current_pick])
            player_name, player_position = self.drafters[self.current_pick].getCurrentAction(
                current_state, self.get_available_players())
            team_id = self.current_pick
            round_num = self.current_round
            self.pick_player(player_name, player_position)
            next_state = State(self.rosters[team_id])
            reward = 0
            if round_num >= self.num_rounds:
                schedule = simulate2.create_schedule(self.num_teams)
                reward = simulate2.ideal_simulate_season(schedule, self.rosters)[
                    "Total Points Scored"][team_id]
            self.drafters[team_id].update(
                current_state, next_state, reward)

    def get_results(self):
        """
        Returns the results of the draft.
        """
        with open("data/draft_results.txt", "a") as file:
            # for team in self.drafters:
            #     file.write("Team: " + str(team.team_id) + "\n")
            #     file.write(str(team.q_values) + "\n\n")
            self.current_pick = 0
            self.current_round = 1
            self.end_draft = False
            self.available_players = copy.deepcopy(self.initial_players)
            self.rosters = copy.deepcopy(self.empty_rosters)
            while not self.get_end_draft():
                current_state = State(self.rosters[self.current_pick])
                if self.current_pick == 0:
                    player_name, player_position = self.drafters[self.current_pick].getPolicy(
                        current_state, self.get_available_players())
                else:
                    player_name, player_position = self.drafters[self.current_pick].getBestAction(
                        current_state, self.get_available_players())
                team_id = self.current_pick
                round_num = self.current_round
                self.pick_player(player_name, player_position)
                output_string = "Round " + str(round_num) + ", Pick " + str(
                    team_id) + ": " + player_name + ", " + player_position + "\n"
                file.write(output_string)
            schedule = simulate2.create_schedule(self.num_teams)
            points_scored = simulate2.ideal_simulate_season(schedule, self.rosters)[
                "Total Points Scored"]
            for team_num in range(self.num_teams):
                output_string = "Team: " + \
                    str(team_num) + ": " + str(points_scored[team_num]) + "\n"
                file.write(output_string)
        with open('data/draft_results_pickled.pkl', 'rb') as inp:
            previous_drafters = pickle5.load(inp)
        for i in range(self.num_teams):
            previous_drafters[i].values.update(self.drafters[i].values)
        with open("data/draft_results_pickled.pkl", 'wb') as outp:
            pickle5.dump(previous_drafters, outp, pickle5.HIGHEST_PROTOCOL)


class State:
    """
    Represents the state of the draft at a moment.
    The State keeps track of the players already picked on their roster.
    """

    def __init__(self, rosters):
        """
        Initializes the state with rosters as the team's current roster of players
        already picked.
        """
        self.rosters = rosters

    def get_rosters(self):
        """
        Returns the rosters of the state.
        """
        return self.rosters


class ValueIterationDrafter:
    """
    Represents a team that is drafting and learning who to draft by keeping
    track of the values using value iteration. A state is defined in the class
    State and an action is a selection of a player. The reward is the total
    number of points scored during the whole fantasy football season using
    idealized lineups for every week. There is no discount rate for rewards
    and transitions are deterministic.
    """

    def __init__(self, team_id, learning_rate, exploration_rate):
        """
        Initializes a Value Iteration Drafter to having the team_id pick in the
        draft with learning_rate for value updates and exploration_rate for
        the chance to explore new actions instead of the current best action.
        """
        self.team_id = team_id
        self.alpha = learning_rate
        self.exp_rate = exploration_rate
        self.values = {}

    def getValue(self, state):
        """
        Gives the Value of a state. Returns 0 if this state has not been
        explored yet.
        """
        try:
            return self.values[state]
        except:
            return 0.0

    def getBestAction(self, state, available_players):
        """
        Returns the best action from the given state. This is the action that
        gives the biggest Value from state.
        """
        if len(available_players) == 0:
            return None
        else:
            best_action_value = float('-inf')
            best_actions = []
            for action in available_players:
                action_roster = state.get_rosters()
                action_roster[action[1]].add(action[0])
                action_value = self.getValue(State(action_roster))
                if action_value == best_action_value:
                    best_actions.append(action)
                elif action_value > best_action_value:
                    best_actions = [action]
                    best_action_value = action_value
                action_roster[action[1]].remove(action[0])
            return random.choice(best_actions)

    def getCurrentAction(self, state, available_players):
        """
        Returns the action that the Value Iteration Drafter should take from state.
        The Drafter will explore with rate self.exp_rate, and take the current
        optimal action with rate 1 - self.exp_rate.
        """
        if len(available_players) == 0:
            return None
        else:
            if random.random() < self.exp_rate:
                return random.choice(available_players)
            else:
                return self.getBestAction(state, available_players)

    def update(self, state, nextState, reward):
        """
        Updates the Values in self.values with the new sample information.
        """
        sample = reward + \
            self.getValue(nextState)
        self.values[state] = (1 - self.alpha) * \
            self.getValue(state) + (self.alpha * sample)

    def getPolicy(self, state, available_players):
        """
        Returns the action to take from state with available_players according
        to the current policy.
        """
        with open("data/draft_results.txt", "a") as file:
            file.write("\nRoster: \n")
            file.write(str(state.get_rosters()) + "\n")
            file.write("Available Players: \n")
            file.write("Values: \n")
            file.write(str(self.values))
            if len(available_players) == 0:
                return None
            else:
                best_action_value = float('-inf')
                best_actions = []
                for action in available_players:
                    action_roster = state.get_rosters()
                    action_roster[action[1]].add(action[0])
                    action_value = self.getValue(State(action_roster))
                    if action_value == best_action_value:
                        best_actions.append(action)
                    elif action_value > best_action_value:
                        best_actions = [action]
                        best_action_value = action_value
                    action_roster[action[1]].remove(action[0])
                return random.choice(best_actions)
