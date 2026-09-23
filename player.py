class Player:
    def __init__(self, name, agent = None):
        self.name = name
        self.hand = []
        self.agent = agent

    def add_card(self, card):
        self.hand.append(card)

    def remove_card(self, card):
        self.hand.remove(card)

    def hand_size(self):
        return len(self.hand)

    def has_won(self):
        return len(self.hand) == 0

    def show_hand(self):
        print(" | ".join(
            f'({i}) {card["value"]} {card["color"]}'
            for i, card in enumerate(self.hand, 1)
        ))