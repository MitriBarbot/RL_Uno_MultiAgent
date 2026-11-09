from game import UnoGame
import random
import pandas as pd
from agents.heuristic_agent import HeuristicAgent
from player import Player
from agents.random_agent import RandomAgent
from environment import UnoEnv
from agents.dqn_agent import DQNAgent


learning_agent = DQNAgent("DQN 1")

players = [
    Player("P1 DQN", learning_agent),
    Player("P2", RandomAgent("Random 2")),
    Player("P3", RandomAgent("Random 3")),
    Player("P4", RandomAgent("Random 4")),
]


learning_player = players[0]

env = UnoEnv(players, learning_player)
