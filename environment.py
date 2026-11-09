from game import UnoGame
import random
import pandas as pd
from agents.heuristic_agent import HeuristicAgent
from player import Player
from agents.random_agent import RandomAgent


class UnoEnv:

    def __init__(self, players, learning_player):
        self.game = UnoGame(players)
        self.learning_player = learning_player
        self.players = players
        self.action_type = None
        self.last_drawn_card = None
        self.players_hand_len = []


    def build_action_space(self):
        cards = pd.read_csv("data/data.csv")
        cards = cards.drop_duplicates()
        

    def reset(self):
        ...

    def step(self, action):
        ...

    def encode_observation(self):
        ...

    def get_action_mask(self):
        ...

    