import pytest

from game import UnoGame, COLORS
from player import Player
from agents.random_agent import RandomAgent
from agents.heuristic_agent import HeuristicAgent


def card(color, value, effect="None"):
    return {"color": color, "value": value, "effect": effect}


@pytest.fixture
def players():
    return [
        Player("P1", RandomAgent("Random 1")),
        Player("P2", RandomAgent("Random 2")),
        Player("P3", RandomAgent("Random 3")),
        Player("P4", RandomAgent("Random 4")),
    ]


@pytest.fixture
def game(players):
    g = UnoGame(players)
    g.current_player = players[0]
    g.last_played = card("Red", "5")
    g.current_color = "Red"
    g.used = [g.last_played]
    return g


# ---------------- Player ----------------

def test_player_starts_empty():
    p = Player("P1", RandomAgent("R"))
    assert p.hand == []
    assert p.hand_size() == 0
    assert p.has_won() is True


def test_player_add_remove_card():
    p = Player("P1", RandomAgent("R"))
    c = card("Red", "3")
    p.add_card(c)
    assert c in p.hand
    assert p.hand_size() == 1
    assert p.has_won() is False
    p.remove_card(c)
    assert p.hand == []
    assert p.has_won() is True


# ---------------- legal_cards ----------------

def test_same_color_is_legal(game):
    c = card("Red", "9")
    game.current_player.hand = [c]
    assert c in game.legal_cards()


def test_same_value_is_legal(game):
    c = card("Blue", "5")
    game.current_player.hand = [c]
    assert c in game.legal_cards()


def test_wild_is_legal(game):
    c = card("Black", "Wild", "Wild")
    game.current_player.hand = [c]
    assert c in game.legal_cards()


def test_wrong_color_and_value_is_illegal(game):
    c = card("Blue", "9")
    game.current_player.hand = [c]
    assert c not in game.legal_cards()


def test_current_color_is_used_after_wild(game):
    game.last_played = card("Black", "Wild", "Wild")
    game.current_color = "Blue"
    blue = card("Blue", "8")
    red = card("Red", "2")
    game.current_player.hand = [blue, red]
    legal = game.legal_cards()
    assert blue in legal
    assert red not in legal


# ---------------- next_player ----------------

def test_next_player_normal(game, players):
    game.current_player = players[0]
    game.next_player()
    assert game.current_player == players[1]


def test_next_player_wraps(game, players):
    game.current_player = players[3]
    game.next_player()
    assert game.current_player == players[0]


def test_next_player_reverse(game, players):
    game.current_player = players[0]
    game.normal_order = False
    game.next_player()
    assert game.current_player == players[3]


# ---------------- play_card ----------------

def test_play_legal_card(game):
    c = card("Red", "8")
    game.current_player.hand = [c]
    result = game.play_card(1)
    assert result is True
    assert game.current_player.hand == []
    assert game.last_played == c
    assert game.used[-1] == c


def test_play_illegal_card_returns_false(game):
    c = card("Blue", "9")
    game.current_player.hand = [c]
    result = game.play_card(1)
    assert result is False
    assert c in game.current_player.hand


@pytest.mark.parametrize("choice", [0, -1, 999, "hello", None, 1.5])
def test_play_card_invalid_choice_returns_false(game, choice):
    game.current_player.hand = [card("Red", "8")]
    assert game.play_card(choice) is False


# ---------------- winner ----------------

def test_player_wins_when_playing_last_card(game):
    game.current_player.hand = [card("Red", "8")]
    game.play_card(1)
    assert game.running is False
    assert game.winner == "P1"


@pytest.mark.parametrize("special_card", [
    card("Red", "Skip", "Skip"),
    card("Red", "Reverse", "Reverse"),
    card("Red", "Draw Two", "Draw Two"),
])
def test_player_can_win_with_special_last_card(game, special_card):
    game.current_player.hand = [special_card]
    assert game.play_card(1) is True
    assert game.running is False
    assert game.winner == "P1"


def test_check_winner_true_when_hand_empty(game):
    game.current_player.hand = []
    assert game.check_winner() is True
    assert game.running is False
    assert game.winner == "P1"


def test_winner_name_remains_after_current_player_changes(game, players):
    game.current_player = players[0]
    game.current_player.hand = []
    game.check_winner()
    game.next_player()
    assert game.current_player == players[1]
    assert game.winner == "P1"


# ---------------- draw_card / play_turn ----------------

def test_draw_card_adds_card(game):
    c = card("Green", "3")
    game.deck = [c]
    drawn = game.draw_card()
    assert drawn == c
    assert c in game.current_player.hand
    assert game.deck == []


def test_empty_deck_recycles_discard(game):
    old1 = card("Blue", "2")
    old2 = card("Green", "4")
    top = card("Red", "5")
    game.deck = []
    game.used = [old1, old2, top]
    drawn = game.draw_card()
    assert drawn in [old1, old2]
    assert game.used == [top]
    assert len(game.deck) == 1


def test_draw_non_playable_card_ends_turn(game, players):
    game.current_player = players[0]
    game.deck = [card("Green", "9")]
    result = game.play_turn(0)
    assert result == "DRAWN"
    assert game.current_player == players[1]


def test_draw_playable_card_returns_drawn_playable(game, players):
    game.current_player = players[0]
    game.deck = [card("Red", "9")]
    result = game.play_turn(0)
    assert result == "DRAWN_PLAYABLE"
    assert game.current_player == players[0]
    assert game.current_player.hand[-1] == card("Red", "9")


# ---------------- effects ----------------

def test_skip_skips_one_player(game, players):
    game.current_player = players[0]
    game.last_played = card("Red", "Skip", "Skip")
    game.apply_effect()
    game.next_player()
    assert game.current_player == players[2]


def test_reverse_changes_direction(game):
    game.normal_order = True
    game.last_played = card("Red", "Reverse", "Reverse")
    game.apply_effect()
    assert game.normal_order is False


def test_two_reverse_restore_direction(game):
    game.normal_order = True
    game.last_played = card("Red", "Reverse", "Reverse")
    game.apply_effect()
    game.apply_effect()
    assert game.normal_order is True


def test_draw_two_draws_exactly_two(game, players):
    game.current_player = players[0]
    game.deck = [card("Yellow", "1"), card("Blue", "2"), card("Green", "3")]
    game.last_played = card("Red", "Draw Two", "Draw Two")
    game.apply_effect()
    assert game.current_player == players[1]
    assert len(players[1].hand) == 2
    assert len(game.deck) == 1


def test_wild_changes_current_color(game, monkeypatch):
    game.last_played = card("Black", "Wild", "Wild")
    monkeypatch.setattr(game.current_player.agent, "choose_action", lambda *args, **kwargs: 2)
    game.apply_effect()
    assert game.current_color == "Blue"


@pytest.mark.parametrize("choice, expected_color", [(1, "Red"), (2, "Blue"), (3, "Yellow"), (4, "Green")])
def test_wild_accepts_all_colors(game, monkeypatch, choice, expected_color):
    game.last_played = card("Black", "Wild", "Wild")
    monkeypatch.setattr(game.current_player.agent, "choose_action", lambda *args, **kwargs: choice)
    game.apply_effect()
    assert game.current_color == expected_color


def test_draw_four_draws_exactly_four(game, players, monkeypatch):
    game.current_player = players[0]
    game.deck = [
        card("Red", "1"), card("Blue", "2"), card("Green", "3"),
        card("Yellow", "4"), card("Red", "5")
    ]
    game.last_played = card("Black", "Wild Draw Four", "Draw Four")
    monkeypatch.setattr(game.current_player.agent, "choose_action", lambda *args, **kwargs: 3)
    game.apply_effect()
    assert game.current_color == "Yellow"
    assert game.current_player == players[1]
    assert len(players[1].hand) == 4
    assert len(game.deck) == 1


def test_draw_four_penalized_player_is_skipped_after_next_player(game, players, monkeypatch):
    game.current_player = players[0]
    game.deck = [
        card("Red", "1"), card("Blue", "2"), card("Green", "3"),
        card("Yellow", "4"), card("Red", "5")
    ]
    game.last_played = card("Black", "Wild Draw Four", "Draw Four")
    monkeypatch.setattr(game.current_player.agent, "choose_action", lambda *args, **kwargs: 1)
    game.apply_effect()
    game.next_player()
    assert game.current_player == players[2]


# ---------------- agents ----------------

def test_random_agent_draws_when_no_legal_action():
    agent = RandomAgent("R")
    hand = [card("Red", "1")]
    action = agent.choose_action(observation=hand, legal_actions=[], action_type="card")
    assert action == 0


def test_random_agent_color_choice_is_valid():
    agent = RandomAgent("R")
    for _ in range(50):
        action = agent.choose_action(observation=[], legal_actions=COLORS, action_type="color")
        assert 1 <= action <= 4


def test_heuristic_prefers_non_black_card():
    agent = HeuristicAgent("H")
    normal = card("Red", "7")
    wild = card("Black", "Wild", "Wild")
    hand = [wild, normal]
    action = agent.choose_action(observation=hand, legal_actions=[wild, normal], action_type="card")
    assert action == 2


def test_heuristic_chooses_most_frequent_color():
    agent = HeuristicAgent("H")
    hand = [
        card("Blue", "1"), card("Blue", "2"), card("Blue", "3"),
        card("Red", "5"), card("Black", "Wild", "Wild")
    ]
    action = agent.choose_action(observation=hand, legal_actions=COLORS, action_type="color")
    assert action == COLORS.index("Blue") + 1


# ---------------- deck/reset ----------------

def test_create_deck_has_108_cards(players):
    g = UnoGame(players)
    g.create_deck()
    assert len(g.deck) == 108


def test_reset_hand_clears_all_players(game, players):
    for p in players:
        p.hand = [card("Red", "1"), card("Blue", "2")]
    game.reset_hand()
    assert all(p.hand == [] for p in players)
