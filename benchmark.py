from game import UnoGame
from player import Player
from agents.random_agent import RandomAgent
from agents.heuristic_agent import HeuristicAgent

from collections import Counter
import time
import matplotlib.pyplot as plt
import pandas as pd


def run_benchmark(amount=10_000):

    players = [
        Player("P1 Heuristic", HeuristicAgent("Heuristic 1")),
        Player("P2 Random", RandomAgent("Random 2")),
        Player("P3 Heuristic", HeuristicAgent("Heuristic 3")),
        Player("P4 Random", RandomAgent("Random 4")),
    ]

    winners = []
    turns = []

    start_time = time.time()

    for _ in range(amount):
        game = UnoGame(players)

        winner = game.run()

        winners.append(winner)
        turns.append(game.turn_count)

    total_time = time.time() - start_time

    counts = Counter(winners)

    winrates = {
        player: count / amount * 100
        for player, count in counts.items()
    }

    average_turns = sum(turns) / amount

    logs = game.logs
    print("____________LOGS______________")
    print(logs)

    print("______________________________")
    print(f"{amount} games in {total_time:.2f}s")
    print(f"Average turns: {average_turns:.2f}")

    print("_________WINRATE_____________")
    for player, winrate in winrates.items():
        print(f"{player}: {winrate:.2f}%")
    print("______________________________")

    plt.bar(winrates.keys(), winrates.values())
    plt.axhline(25, linestyle="--")
    plt.ylabel("Winrate (%)")
    plt.title(
        f"{amount} games | Average turns: {average_turns:.2f}"
    )

    plt.show()
    replay_logs = game.replay_logs
    print(replay_logs)


if __name__ == "__main__":
    run_benchmark()