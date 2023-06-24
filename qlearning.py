import random
import pickle5


class State:
    """

    """

    def __init__(self, num_teams, roster, scoring_format):
        """
        Initializes the state for a league of num_teams with scoring_format.
        Roster is a dictionary where the keys are positions (i.e. "qb", "rb",
        etc.) and the values are a list of the players on that team's roster
        for that position (which is initially empty).
        """
        self.num_teams = num_teams
        self.scoring_format = scoring_format
        self.available_players = self.getInitialPlayers()
        self.rosters = [roster] * num_teams
        self.current_pick = 0
        self.round = 1

    def getInitialPlayers(self):
        """
        Returns a dictionary of all of the available players to be drafted
        to start.

        The dictionary has a key for each position and the values are another
        dictionary from player names to their gamelogs for each player in
        that position.
        """
        players_dict = {}
        with open('data/qb_STANDARD.pkl', 'rb') as inp:
            players_dict["qb"] = pickle5.load(inp)
        with open('data/rb_' + self.scoring_format + '.pkl', 'rb') as inp:
            players_dict["rb"] = pickle5.load(inp)
        with open('data/wr_' + self.scoring_format + '.pkl', 'rb') as inp:
            players_dict["wr"] = pickle5.load(inp)
        with open('data/te_' + self.scoring_format + '.pkl', 'rb') as inp:
            players_dict["te"] = pickle5.load(inp)
        with open('data/dst_STANDARD.pkl', 'rb') as inp:
            players_dict["dst"] = pickle5.load(inp)
        with open('data/k_STANDARD.pkl', 'rb') as inp:
            players_dict["k"] = pickle5.load(inp)
        return players_dict

    def pick_player(self, player_name, player_position):
        """
        Simulates drafting a player from the available players.
        """
        player_pick = self.available_players[player_position].pop(player_name)
        self.rosters[self.current_pick].append((player_name, player_pick))
        if self.round % 2 == 1:
            if self.current_pick < self.num_teams - 1:
                self.current_pick += 1
            else:
                self.round += 1
        else:
            if self.current_pick > 0:
                self.current_pick -= 1
            else:
                self.round += 1


class QLearningDrafter:
    """
    States: rosters of the individual teams
    Actions: Draft selections
    Rewards: Total points scored at the end of the year
    """

    def __init__(self, num_teams, learning_rate, exploration_rate):
        self.num_teams = num_teams
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
        available_actions = self.getAvailablePlayers(state)
        if self.endDraft(state):
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
        available_actions = self.getAvailablePlayers(state)
        if self.endDraft(state):
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
        available_actions = self.getAvailablePlayers(state)
        if self.endDraft(state):
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


initial_state = State(14, None, "HALF")
