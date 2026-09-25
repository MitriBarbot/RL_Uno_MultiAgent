from game import UnoGame
from agents.heuristic_agent import HeuristicAgent
from player import Player
from agents.random_agent import RandomAgent
from collections import Counter
import time
import matplotlib.pyplot as plt

logs = {"Winner" : [], "Turns" : []}
start_time = time.time()
ammount = 10000

players = [
    Player("P1 Heuristic", HeuristicAgent("Heuristic 1")),
    Player("P2", RandomAgent("Random 2")),
    Player("P3 Heuristic", HeuristicAgent("Heuristic 3")),
    Player("P4", RandomAgent("Random 4")),
]

for i in range(ammount):
    game = UnoGame(players)
    winner = game.run()
    logs["Winner"].append(winner)
    logs["Turns"].append(game.turn_count)
    #print(winner)
    #print("\n".join(game.logs))
end_time = time.time()
total_time = end_time - start_time
print(game.logs)
#print(Counter(logs))
print(f"Time needed: {total_time:.2f} seconds for {ammount} games")
counts = Counter(logs["Winner"])
average_turn = sum(logs["Turns"]) / ammount
winrate = {}
for i in counts.keys():
    print(i, "winrate", counts[i]/ammount *100)
    winrate[i] = counts[i]/ammount *100
plt.bar(counts.keys(), winrate.values())
plt.xlabel("Player")
plt.ylabel("Wins")
plt.title(f"Winrate over {ammount} games, average turn = {average_turn:.2f}")
plt.axhline(25, linestyle="--", label="Average winrate with 4 RandomAgent", c="red")
plt.legend()

plt.show()