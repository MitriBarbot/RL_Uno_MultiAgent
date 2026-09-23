from game import UnoGame, players
from collections import Counter
import time
import matplotlib.pyplot as plt

logs = []
start_time = time.time()
ammount = 1000

for i in range(ammount):
    game = UnoGame(players)
    winner = game.run()
    logs.append(winner)
    #print(winner)
    #print("\n".join(game.logs))
end_time = time.time()
total_time = end_time - start_time

print(Counter(logs))
print(f"Time needed: {total_time:.2f} seconds for {ammount} games")
counts = Counter(logs)


plt.bar(counts.keys(), counts.values())
plt.xlabel("Player")
plt.ylabel("Wins")
plt.title("Winrate over 1000 games")
plt.legend()

plt.show()