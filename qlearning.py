import random
import pickle5
import numpy as np
import simulate


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
        """
        self.num_teams = num_teams
        self.current_pick = 0
        self.current_round = 1
        self.num_rounds = num_rounds
        self.end_draft = False
        self.initial_players = self.get_initial_players()
        self.available_players = self.initial_players
        self.empty_rosters = [roster] * num_teams
        self.rosters = self.empty_rosters
        self.scoring_format = scoring_format
        self.drafters = [QLearningDrafter(i, 0.2, 0.05)
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
            if len(gamelog_list) > 0:
                new_dict[player] = np.array(
                    [0.0 if type(i) != float else i for i in gamelog_list])
        return new_dict

    def pick_player(self, player_name, player_position):
        """
        Simulates drafting a player from the available players. Also checks
        and sets self.endDraft to true if this is the end of the draft.
        """
        player_pick = self.available_players[player_position].pop(player_name)
        self.rosters[self.current_pick].append(player_pick)
        if self.current_round % 2 == 1:
            if self.current_pick < self.num_teams - 1:
                self.current_pick += 1
            else:
                self.current_round += 1
                if self.current_round > self.num_rounds:
                    self.endDraft = True
        else:
            if self.current_pick > 0:
                self.current_pick -= 1
            else:
                self.current_round += 1
                if self.current_round > self.num_rounds:
                    self.endDraft = True

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
        for training_episode in range(self.num_training):
            if self.get_end_draft():
                self.current_pick = 0
                self.current_round = 1
                self.end_draft = False
                self.available_players = self.initial_players
                self.rosters = self.empty_rosters
            current_state = State(self.available_players, self.rosters)
            player_name, player_position = self.drafters[self.current_pick].getCurrentAction(
                current_state)
            team_id = self.current_pick
            self.pick_player(player_name, player_position)
            next_state = State(self.available_players, self.rosters)
            reward = 0
            if self.current_round >= self.num_rounds:
                schedule = simulate.create_schedule(self.num_teams)
                reward = simulate.ideal_simulate_season(schedule, self.rosters)[
                    "Total Points Scored"][team_id]
            self.drafters[team_id].update(
                current_state, (player_name, player_position), next_state, reward)


class State:
    """
    Represents the state of the draft at a moment.
    The State keeps track of the players already picked on each roster and the
    available players to be drafted.
    """

    def __init__(self, available_players, rosters):
        """
        Initializes the state with available_players still available to be
        drafted by a team and rosters as the teams current rosters of players
        already picked.
        """
        self.available_players = available_players
        self.rosters = rosters

    def get_available_players(self):
        """
        Returns the available players to be drafted.
        """
        all_positions_list = []
        for position in self.available_players:
            for player_name in self.available_players[position]:
                all_positions_list.append((player_name, position))
        return all_positions_list

    def get_rosters(self):
        """
        Returns the rosters of the state.
        """
        return self.rosters


class QLearningDrafter:
    """
    Represents a team that is drafting and learning who to draft by keeping
    track of the q-values using q-learning. A state is defined in the class
    State and an action is a selection of a player. The reward is the total
    number of points scored during the whole fantasy football season using
    idealized lineups for every week. There is no discount rate for rewards
    and transitions are deterministic.
    """

    def __init__(self, team_id, learning_rate, exploration_rate):
        """
        Initializes a Q-Learning Drafter to having the team_id pick in the
        draft with learning_rate for q-value updates and exploration_rate for
        the chance to explore new actions instead of the current best action.
        """
        self.team_id = team_id
        self.alpha = learning_rate
        self.exp_rate = exploration_rate
        self.q_values = {}

    def getQValue(self, state, action):
        """
        Gives the Q-Value of a state and action. Returns 0 if this state and
        action pair has not been explored yet.
        """
        try:
            return self.q_values[(state, action)]
        except:
            return 0.0

    def getValues(self, state):
        """
        Gives the Value of a state. This is the max value that can be obtained
        from the actions in this state.
        """
        available_actions = state.get_available_players()
        if len(available_actions) == 0:
            return 0.0
        else:
            best_action = float('-inf')
            for action in available_actions:
                best_action = max(best_action, self.getQValue(state, action))
            return best_action

    def getBestAction(self, state):
        """
        Returns the best action from the given state. This is the action that
        gives the biggest Q-Value from state.
        """
        available_actions = state.get_available_players()
        if len(available_actions) == 0:
            return None
        else:
            best_action_value = float('-inf')
            best_actions = []
            for action in available_actions:
                action_q_value = self.getQValue(state, action)
                if action_q_value == best_action_value:
                    best_actions.append(action)
                elif action_q_value > best_action_value:
                    best_actions = [action]
                    best_action_value = action_q_value
            return random.choice(best_actions)

    def getCurrentAction(self, state):
        """
        Returns the action that the Q-Learning Drafter should take from state.
        The Drafter will explore with rate self.exp_rate, and take the current
        optimal action with rate 1 - self.exp_rate.
        """
        available_actions = state.get_available_players()
        if len(available_actions) == 0:
            return None
        else:
            if random.random() < self.exp_rate:
                return random.choice(available_actions)
            else:
                return self.getBestAction(state)

    def update(self, state, action, nextState, reward):
        """
        Updates the Q-Values in self.q_values with the new sample information.
        """
        sample = reward + \
            self.getQValue(nextState, self.getBestAction(nextState))
        self.q_values[(state, action)] = ((1 - self.alpha) *
                                          self.getQValue(state, action)) + (self.alpha * sample)


initial_state = State(14, None, "HALF", 20)
print(initial_state.getAvailablePlayers())
