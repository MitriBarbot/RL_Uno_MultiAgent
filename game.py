import random
import pandas as pd
from agents.heuristic_agent import HeuristicAgent
from player import Player
from agents.random_agent import RandomAgent


COLORS = ["Red", "Blue", "Yellow", "Green"]


class UnoGame:
    def __init__(self, players):
        self.players = players
        self.deck = []
        self.used = []
        self.current_player = None
        self.last_played = None
        self.normal_order = True
        self.running = True
        self.winner = None
        self.turn_count = 0
        self.current_color = None
        self.logs = []
        self.replay_logs = {
            "setup" : {},
            "turns" : [],
            "result" : {}
        }

    def create_deck(self):
        self.deck = []
        card_df = pd.read_csv("data/data.csv")
        for _, row in card_df.iterrows():
            for _ in range(row["count"]):
                self.deck.append({
                    "color": row["color"],
                    "value": row["value"],
                    "effect": None if pd.isna(row["effect"]) else row["effect"]
                })


    
    def shuffle_deck(self):
        random.shuffle(self.deck)


    def deal_cards(self):
        for player in self.players:
            for _ in range(7):
                player.hand.append(self.deck.pop())

    def draw_card(self):
        if not self.deck:
            last_card = self.used.pop()
            self.deck = self.used
            random.shuffle(self.deck)
            self.used = [last_card]
        card = self.deck.pop()
        self.current_player.hand.append(card)
        return card

    def reset_hand(self):
        for player in self.players:
            player.hand = []


    def legal_cards(self):
        legal = []

        has_current_color = any(
            card["color"] == self.current_color
            for card in self.current_player.hand
        )

        for card in self.current_player.hand:

            if card["effect"] == "Wild":
                legal.append(card)

            # +4 seulement si aucune carte de la couleur active
            elif card["effect"] == "Draw Four":
                if not has_current_color:
                    legal.append(card)

            elif card["color"] == self.current_color:
                legal.append(card)

            elif card["value"] == self.last_played["value"]:
                legal.append(card)

        return legal

    def next_player(self):
        if self.current_player is None:
            self.current_player = random.choice(self.players) #random player starts
            
            #self.current_player = self.players[0] #player1 starts 
            return

        index = self.players.index(self.current_player)

        if self.normal_order:
            self.current_player = self.players[
                (index + 1) % len(self.players)
            ]
        else:
            self.current_player = self.players[
                (index - 1) % len(self.players)
            ]

    def play_turn(self, choice=None):
        self.turn_count += 1
        self.log_turns({
            "turn": self.turn_count,
            "player": self.current_player.name,
            "events": []
        })

        if choice is None or choice == 0:
            drawn_card = self.draw_card()
            self.log_event({
                            "type": "DRAW",
                            "player": self.current_player.name,
                            "cards": [drawn_card]
                            })

            if drawn_card in self.legal_cards():
                return "DRAWN_PLAYABLE"

            self.next_player()
            return "DRAWN"

        success = self.play_card(choice)

        if success:
            if not self.running:
                return True

            self.apply_effect()
            self.next_player()
            return True

        return False


    def check_winner(self):
        if len(self.current_player.hand) == 0:
            self.winner = self.current_player.name
            self.log(f"{self.winner} won the game !")
            self.running = False
            self.log_result({"Winner" : self.winner, "Turns_count" : self.turn_count})
            return True

        return False

    def apply_effect(self):
        effect = self.last_played["effect"]

        if effect == "Skip":
            self.next_player()

        elif effect == "Reverse":
            self.normal_order = not self.normal_order
            self.log_event({"type": "DIRECTION_CHANGE",
                            "direction": "clockwise" if self.normal_order else "counter_clockwise"})

        elif effect == "Draw Two":
            self.next_player()
            drawn_card = [self.draw_card() for _ in range(2)]
            self.log_event({
                        "type": "DRAW",
                        "player": self.current_player.name,
                        "cards": drawn_card
                        })
            

        elif effect == "Draw Four":
            new_color = self.ask_color()
            self.current_color = COLORS[new_color - 1]
            self.log_event({
                            "type": "COLOR_CHANGE",
                            "player": self.current_player.name,
                            "new_color": self.current_color
                            })
            self.next_player()
            
            drawn_card = [self.draw_card() for _ in range(4)]
            self.log_event({
                                "type": "DRAW",
                                "player": self.current_player.name,
                                "cards": drawn_card
                                })

        elif effect == "Wild":
            new_color = self.ask_color()
            self.current_color = COLORS[new_color - 1]
            self.log_event({
                            "type": "COLOR_CHANGE",
                            "player": self.current_player.name,
                            "new_color": self.current_color
                            })
            

    def apply_starting_effect(self):
        effect = self.last_played["effect"]
        events = self.replay_logs["setup"]["events"]

        if effect == "Skip":
            skipped = self.current_player.name
            self.next_player()
            events.append({"type": "SKIP",
                           "player": skipped})

        elif effect == "Reverse":
            self.normal_order = not self.normal_order
            self.next_player()
            events.append({"type": "DIRECTION_CHANGE",
                           "direction": "clockwise" if self.normal_order else "counter_clockwise"})

        elif effect == "Draw Two":
            penalized = self.current_player.name
            drawn_card = [self.draw_card() for _ in range(2)]
            events.append({"type": "DRAW",
                           "player": penalized,
                           "cards": drawn_card})
            self.next_player()

        elif effect == "Wild":
            color_choice = self.ask_color()
            self.current_color = COLORS[color_choice -1]
            events.append({"type": "COLOR_CHANGE",
                           "color": self.current_color})
            


    def play_card(self, choice):
        if not isinstance(choice, int):
            return False

        if choice < 1 or choice > len(self.current_player.hand):
            return False

        card = self.current_player.hand[choice -1]

        if card not in self.legal_cards():
            return False

        played_card = self.current_player.hand.pop(choice -1)

        self.used.append(played_card)
        self.last_played = played_card
        self.log_event({
                                    "type": "PLAY",
                                    "player": self.current_player.name,
                                    "card": played_card.copy()
                                    })
        #self.log(f"{self.current_player.name} , played | {played_card['value']} {played_card['color']}")
        self.current_color = played_card["color"]

        self.check_winner()

        return True


    def setup_round(self):
        self.current_player = None
        self.normal_order = True
        self.running = True
        self.winner = None
        self.turn_count = 0

        self.used = []
        self.logs = []

        self.replay_logs = {
            "setup": {},
            "turns": [],
            "result": {}
        }
        self.reset_hand()
        self.create_deck()
        self.shuffle_deck()
        self.deal_cards()

        first_card = self.deck.pop()
        while first_card["effect"] == "Draw Four":
            self.deck.insert(0, first_card)
            self.shuffle_deck()
            first_card = self.deck.pop()
        self.used.append(first_card)
        self.last_played = first_card
        self.current_color = first_card["color"]
        self.next_player()
        self.log_setup({
                        "players": {
                            player.name: [
                                card.copy() for card in player.hand
                            ]
                            for player in self.players
                        },
                        "starting_card": first_card.copy(),
                        "starting_player": self.current_player.name,
                        "direction": "clockwise" if self.normal_order else "counter_clockwise",
                        "events": []
                    })
        self.apply_starting_effect()
        self.log_setup({
                        "active_player_after_setup": self.current_player.name,
                        "active_color_after_setup": self.current_color
                    })
        self.log(f"Starting card : {self.last_played['value']} | {self.last_played['color']}")
        self.log(f"First Player: {self.current_player.name}")
        


    def ask_card(self):
        while True:
            choice = input(
                f"Choose a card between 1 and {len(self.current_player.hand)} "
                "or 0 to draw: "
            )

            try:
                choice = int(choice)
            except ValueError:
                print("Please enter an integer.")
                continue

            if 0 <= choice <= len(self.current_player.hand):
                return choice

            print("Choice out of range.")


    def show_last_card(self):
        print(f" | {self.last_played["value"]}  {self.current_color} |")

    def ask_color(self):
        while True:
            choice = self.current_player.agent.choose_action(observation= self.current_player.hand, legal_actions= COLORS , action_type="color")

            try:
                choice = int(choice)
            except ValueError:
                continue

            if 1 <= choice <= 4:
                return choice


    def run(self):
        self.setup_round()

        while self.running:
            player = self.current_player
            agent = player.agent

            observation = self.get_observation()
            legal_actions = self.get_legal_actions()

            action = agent.choose_action(
                observation,
                legal_actions,
                action_type="card"
            )

            result = self.play_turn(action)

            if result == "DRAWN_PLAYABLE":
                drawn_choice = agent.choose_action(
                    observation=self.get_observation(),
                    legal_actions=[0, 1],
                    action_type="drawn"
                )

                # 0 = pass
                if drawn_choice == 0:
                    self.log_event({
                                    "type": "PASS",
                                    "player": self.current_player.name
                                    })
                    
                    self.next_player()

                # 1 = play the card just drawn
                elif drawn_choice == 1:
                    drawn_card_index = len(self.current_player.hand)

                    success = self.play_card(drawn_card_index)

                    if success and self.running:
                        self.apply_effect()
                        self.next_player()

        return self.winner


    def log_setup(self, setup_data):
        self.replay_logs["setup"].update(setup_data)


    def log_turns(self, turn_data):
            self.replay_logs["turns"].append(turn_data)
    

    def log_result(self, result_data):
            self.replay_logs["result"] = result_data

    def log(self, message):
        self.logs.append(message)
            

    def get_observation(self):
        return self.current_player.hand

    def get_legal_actions(self):
        return self.legal_cards()

    def log_event(self, event_data):
        self.replay_logs["turns"][-1]["events"].append(event_data)