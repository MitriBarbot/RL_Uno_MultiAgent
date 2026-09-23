class Agent:
    def __init__(self, name):
        self.name = name

    def choose_action(self, observation, legal_actions, action_type):
        raise NotImplementedError

