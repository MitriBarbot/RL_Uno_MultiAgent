"""Targeted UNO rules regression tests.

Place in tests/test_uno_edge_cases.py, keeping your existing test_game.py.
Assumptions: 4 players, UnoGame(players), setup_round(), legal_cards(),
play_turn(0), and official/classic first-card action rules.

Tests use deterministic deck/starting player, independent of data/data.csv.
"""

import pytest
from game import UnoGame
from player import Player
from agents.random_agent import RandomAgent


def card(color, value, effect=None):
    return {"color": color, "value": value, "effect": effect}


@pytest.fixture
def players():
    return [Player(f"P{i}", RandomAgent(f"Random {i}")) for i in range(1, 5)]


@pytest.fixture
def game(players):
    return UnoGame(players)


def start_with(game, monkeypatch, first_card, *, next_start_card=None):
    """Force a first card and deterministic starting player (P1).

    Layout: bottom cards, initial card, 28 cards dealt off the top.
    For +4 replacement, next_start_card remains immediately below the +4.
    """
    extra = [card("Green", str(i % 10)) for i in range(12)]
    bottom = extra + ([next_start_card] if next_start_card is not None else [])
    game_deck = bottom + [first_card] + [card("Yellow", "7") for _ in range(28)]

    monkeypatch.setattr(game, "create_deck", lambda: setattr(game, "deck", list(game_deck)))
    monkeypatch.setattr(game, "shuffle_deck", lambda: None)
    # The first player chosen through random.choice(self.players) is P1.
    monkeypatch.setattr("game.random.choice", lambda seq: seq[0])
    # When initial Wild is displayed, P1 must be able to choose Blue.
    for p in game.players:
        monkeypatch.setattr(p.agent, "choose_action", lambda *args, **kwargs: 2)
    game.setup_round()
    return game


# ---- Initial card behavior ----

def test_start_number_card_sets_color_and_7_cards(game, players, monkeypatch):
    start_with(game, monkeypatch, card("Red", "5"))
    assert game.last_played == card("Red", "5")
    assert game.current_color == "Red"
    assert game.current_player is players[0]
    assert all(len(p.hand) == 7 for p in players)


def test_start_wild_selects_a_real_color_without_forced_draw(game, players, monkeypatch):
    start_with(game, monkeypatch, card("Black", "Wild", "Wild"))
    assert game.current_color == "Blue", "An initial Wild must choose an active color."
    assert game.current_player is players[0]
    assert all(len(p.hand) == 7 for p in players), "Wild at setup does not force draws."


def test_after_initial_wild_matching_color_is_playable_without_wild(game, monkeypatch):
    start_with(game, monkeypatch, card("Black", "Wild", "Wild"))
    blue = card("Blue", "2")
    red = card("Red", "9")
    game.current_player.hand = [blue, red]
    legal = game.legal_cards()
    assert blue in legal
    assert red not in legal


def test_start_skip_skips_intended_first_player(game, players, monkeypatch):
    start_with(game, monkeypatch, card("Red", "Skip", "Skip"))
    assert game.current_player is players[1]


def test_start_reverse_changes_direction(game, monkeypatch):
    start_with(game, monkeypatch, card("Red", "Reverse", "Reverse"))
    assert game.normal_order is False


def test_start_draw_two_penalizes_and_skips_first_player(game, players, monkeypatch):
    start_with(game, monkeypatch, card("Red", "Draw Two", "Draw Two"))
    assert len(players[0].hand) == 9
    assert all(len(p.hand) == 7 for p in players[1:])
    assert game.current_player is players[1]


def test_start_wild_draw_four_is_replaced_not_applied(game, players, monkeypatch):
    replacement = card("Red", "3")
    start_with(game, monkeypatch,
               card("Black", "Wild Draw Four", "Draw Four"),
               next_start_card=replacement)
    assert game.last_played != card("Black", "Wild Draw Four", "Draw Four"), (
        "Official classic rules: initial +4 must be returned to draw pile and replaced."
    )
    assert all(len(p.hand) == 7 for p in players)


# ---- Wild / Draw Four legality ----

def test_draw_four_illegal_if_matching_active_color(game, players):
    game.current_player = players[0]
    game.current_color = "Red"
    game.last_played = card("Red", "5")
    wild4 = card("Black", "Wild Draw Four", "Draw Four")
    players[0].hand = [card("Red", "9"), wild4]
    assert wild4 not in game.legal_cards()


def test_draw_four_legal_if_only_matching_number(game, players):
    game.current_player = players[0]
    game.current_color = "Red"
    game.last_played = card("Red", "5")
    wild4 = card("Black", "Wild Draw Four", "Draw Four")
    players[0].hand = [card("Blue", "5"), wild4]
    assert wild4 in game.legal_cards()


def test_regular_wild_remains_playable_with_matching_color(game, players):
    game.current_player = players[0]
    game.current_color = "Red"
    game.last_played = card("Red", "5")
    wild = card("Black", "Wild", "Wild")
    players[0].hand = [card("Red", "9"), wild]
    assert wild in game.legal_cards()


# ---- Draw behavior / finishing ----

def test_draw_playable_keeps_turn_for_follow_up_decision(game, players):
    game.current_player = players[0]
    game.current_color = "Red"
    game.last_played = card("Red", "5")
    game.deck = [card("Red", "8")]
    result = game.play_turn(0)
    assert result == "DRAWN_PLAYABLE"
    assert game.current_player is players[0]


def test_draw_nonplayable_advances_to_next_player(game, players):
    game.current_player = players[0]
    game.current_color = "Red"
    game.last_played = card("Red", "5")
    game.deck = [card("Green", "8")]
    result = game.play_turn(0)
    assert result == "DRAWN"
    assert game.current_player is players[1]
