import random

from agents.base_agent import Agent

class RandomAgent(Agent):
    def choose_action(self, observation= None, legal_actions = None, action_type="card"):
        if action_type == "color":
            return random.randint(1,4)

        if action_type == "drawn":
            return random.choice([0, 1])
        
        if not legal_actions:
            return 0
        card = random.choice(legal_actions)
        return observation.index(card) +1