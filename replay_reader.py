import copy
import json

class ReplayReader:
    def __init__(self, path = "replay.json"):
        self.path = path
        self.replay = None
        self.setup = {}
        self.turns = []
        self.result = {}

        self.hands = {}
        self.current_player = None
        self.current_color = None
        self.last_played = None
        self.direction = "clockwise"

        self.turn_index = 0


    def reset(self):
        self.setup = self.replay["setup"]
        self.turns = self.replay["turns"]
        self.result = self.replay["result"]
        self.hands = copy.deepcopy(self.setup["players"])
        self.current_player = self.setup["active_player_after_setup"]
        self.current_color = self.setup["active_color_after_setup"]
        self.last_played = self.setup["starting_card"].copy()
        self.turn_index = 0
                
        


    def load_replay(self):
        with open(self.path, "r", encoding="utf-8") as f:
            self.replay = json.load(f)