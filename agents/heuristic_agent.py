import random
from agents.base_agent import Agent

class HeuristicAgent(Agent):
    def choose_action(self, observation= None, legal_actions = None, action_type="card"):
        if action_type == "color":
            return self.most_freq_color(legal_actions, observation)

        if action_type == "drawn":
            return 1
        
        if not legal_actions:
            return 0
        non_black_cards = [
        card for card in legal_actions
        if card["color"] != "Black"]

        if non_black_cards:
            card = random.choice(non_black_cards)
            return observation.index(card) + 1
        card = random.choice(legal_actions)
        return observation.index(card) +1

    def most_freq_color(self,legal_actions,hand):
        color_hand = []
        for card in hand:
            if card["color"] != "Black":
                color_hand.append(card["color"])
        if not color_hand:
            return random.randint(1,4)
        
        most_frequent = max(set(color_hand), key=color_hand.count)
        return legal_actions.index(most_frequent) +1
        


