"""Régressions UNO + validation structurée des replays.

Placer dans tests/test_game_complete.py et exécuter :
    python -m pytest tests/test_game_complete.py -v
    python -m pytest tests/test_game_complete.py -v -m "not slow"
    python -m pytest tests/test_game_complete.py -v -m slow

À utiliser en plus des tests existants. Certains tests de replay sont
volontairement stricts : leur échec identifie une donnée manquante ou
un format incohérent, plutôt qu'une erreur de la règle UNO.
"""
from __future__ import annotations

import copy
import json
import random
from collections import Counter

import pytest

from game import COLORS, UnoGame
from player import Player
from agents.random_agent import RandomAgent
from agents.heuristic_agent import HeuristicAgent


def card(color="Red", value="5", effect=None):
    return {"color": color, "value": value, "effect": effect}


@pytest.fixture
def players():
    return [Player(f"P{i}", RandomAgent(f"R{i}")) for i in range(1, 5)]


@pytest.fixture
def game(players):
    g = UnoGame(players)
    g.current_player = players[0]
    g.current_color = "Red"
    g.last_played = card("Red", "5")
    g.used = [g.last_played.copy()]
    return g


def init_turn(g):
    """Créer une entrée de tour, comme play_turn() le fait normalement."""
    g.turn_count += 1
    g.log_turns({"turn": g.turn_count, "player": g.current_player.name, "events": []})


def force_start(game, monkeypatch, first_card, *, extra_card=None):
    """Départ déterministe, sans CSV, avec la première carte contrôlée."""
    deck = [card("Green", str(i % 10)) for i in range(15)]
    if extra_card is not None:
        deck.append(extra_card)
    deck += [first_card] + [card("Yellow", "7") for _ in range(28)]
    monkeypatch.setattr(game, "create_deck", lambda: setattr(game, "deck", copy.deepcopy(deck)))
    monkeypatch.setattr(game, "shuffle_deck", lambda: None)
    monkeypatch.setattr("game.random.choice", lambda seq: seq[0])
    for p in game.players:
        monkeypatch.setattr(p.agent, "choose_action", lambda *args, **kwargs: 2)
    game.setup_round()
    return game


# ─────────── Player, agent, card matching ───────────

def test_player_hand_operations(players):
    p = players[0]
    x = card("Red", "2")
    assert p.hand_size() == 0
    p.add_card(x)
    assert p.hand_size() == 1
    assert not p.has_won()
    p.remove_card(x)
    assert p.has_won()


@pytest.mark.parametrize("hand,expected", [
    ([card("Red", "2")], True),
    ([card("Blue", "5")], True),
    ([card("Green", "3")], False),
    ([card("Black", "Wild", "Wild")], True),
])
def test_legal_card_basics(game, hand, expected):
    game.current_player.hand = hand
    assert (hand[0] in game.legal_cards()) is expected


def test_wild_four_illegal_when_holding_matching_color(game):
    four = card("Black", "Wild Draw Four", "Draw Four")
    game.current_player.hand = [four, card("Red", "8")]
    assert four not in game.legal_cards()


def test_wild_four_legal_with_same_number_but_no_matching_color(game):
    four = card("Black", "Wild Draw Four", "Draw Four")
    game.current_player.hand = [four, card("Blue", "5")]
    assert four in game.legal_cards()


def test_regular_wild_always_legal(game):
    wild = card("Black", "Wild", "Wild")
    game.current_player.hand = [wild, card("Red", "8")]
    assert wild in game.legal_cards()


@pytest.mark.parametrize("choice", [-1, 0, 99, None, "1", 1.2])
def test_invalid_card_choices_preserve_hand_and_discard(game, choice):
    game.current_player.hand = [card("Red", "8")]
    before = copy.deepcopy(game.current_player.hand)
    assert game.play_card(choice) is False
    assert game.current_player.hand == before
    assert game.last_played == card("Red", "5")


def test_duplicate_card_play_removes_exactly_one(game):
    duplicate = card("Red", "7")
    game.current_player.hand = [duplicate.copy(), duplicate.copy(), card("Blue", "1")]
    init_turn(game)
    assert game.play_card(2)
    assert game.current_player.hand.count(duplicate) == 1


def test_win_records_name_and_result(game):
    game.current_player.hand = [card("Red", "8")]
    init_turn(game)
    assert game.play_turn(1)
    assert not game.running
    assert game.winner == "P1"
    assert game.replay_logs["result"]["Winner"] == "P1"
    assert game.replay_logs["result"]["Turns_count"] >= 1


@pytest.mark.parametrize("last_card", [
    card("Red", "Skip", "Skip"),
    card("Red", "Reverse", "Reverse"),
    card("Red", "Draw Two", "Draw Two"),
    card("Black", "Wild", "Wild"),
])
def test_winning_last_card_does_not_continue_turn(game, players, last_card):
    game.current_player.hand = [last_card]
    current = game.current_player
    assert game.play_turn(1) is True
    assert not game.running
    assert game.current_player is current
    assert game.winner == current.name


# ─────────── Turn order and effect ───────────

@pytest.mark.parametrize("start,direction,expected", [
    (0, True, 1),
    (3, True, 0),
    (0, False, 3),
    (2, False, 1),
])
def test_next_player_wrap(game, players, start, direction, expected):
    game.current_player = players[start]
    game.normal_order = direction
    game.next_player()
    assert game.current_player is players[expected]


def test_skip_skips_exactly_one_player(game, players):
    game.current_player.hand = [card("Red", "Skip", "Skip"), card("Green", "1")]
    assert game.play_turn(1)
    assert game.current_player is players[2]


def test_reverse_flips_direction(game, players):
    game.current_player.hand = [card("Red", "Reverse", "Reverse"), card("Green", "1")]
    assert game.play_turn(1)
    assert game.normal_order is False
    assert game.current_player is players[3]


@pytest.mark.parametrize("effect,expected_count", [
    ("Draw Two", 2),
    ("Draw Four", 4),
])
def test_penalty_draws_and_skips(game, players, monkeypatch, effect, expected_count):
    if effect == "Draw Two":
        played = card("Red", "Draw Two", effect)
    else:
        played = card("Black", "Wild Draw Four", effect)
        monkeypatch.setattr(players[0].agent, "choose_action", lambda *a, **k: 2)
    game.current_player.hand = [played, card("Blue", "8")]
    game.deck = [card("Yellow", str(i)) for i in range(10)]
    assert game.play_turn(1)
    assert len(players[1].hand) == expected_count
    assert game.current_player is players[2]
    if effect == "Draw Four":
        assert game.current_color == "Blue"


@pytest.mark.parametrize("chosen_color", [1, 2, 3, 4])
def test_wild_choice_matches_colors(game, players, monkeypatch, chosen_color):
    monkeypatch.setattr(players[0].agent, "choose_action", lambda *a, **k: chosen_color)
    game.current_player.hand = [card("Black", "Wild", "Wild"), card("Green", "1")]
    assert game.play_turn(1)
    assert game.current_color == COLORS[chosen_color - 1]


# ─────────── Drawing ───────────

def test_draw_unplayable_advances(game, players):
    game.deck = [card("Blue", "8")]
    assert game.play_turn(0) == "DRAWN"
    assert game.current_player is players[1]
    assert game.turn_count == 1


def test_draw_playable_stays_with_current_player(game, players):
    game.deck = [card("Red", "8")]
    assert game.play_turn(0) == "DRAWN_PLAYABLE"
    assert game.current_player is players[0]
    assert game.turn_count == 1


def test_recycled_deck_keeps_top_discard(game):
    top = card("Red", "5")
    rest = [card("Green", "1"), card("Blue", "2")]
    game.deck = []
    game.used = rest + [top]
    drawn = game.draw_card()
    assert drawn in rest
    assert game.used == [top]
    assert len(game.deck) == 1


# ─────────── Deterministic starting-card rules ───────────

@pytest.mark.parametrize("first_card,expected_player,expected_direction,expected_color,penalty", [
    (card("Red", "5"), 0, True, "Red", 0),
    (card("Red", "Skip", "Skip"), 1, True, "Red", 0),
    (card("Red", "Reverse", "Reverse"), 3, False, "Red", 0),
    (card("Red", "Draw Two", "Draw Two"), 1, True, "Red", 2),
    (card("Black", "Wild", "Wild"), 0, True, "Blue", 0),
])
def test_starting_card_effects(players, monkeypatch, first_card,
                                expected_player, expected_direction, expected_color, penalty):
    g = UnoGame(players)
    force_start(g, monkeypatch, first_card)
    assert g.current_player is players[expected_player]
    assert g.normal_order is expected_direction
    assert g.current_color == expected_color
    assert len(players[0].hand) == 7 + penalty
    assert g.turn_count == 0
    assert len(g.replay_logs["turns"]) == 0


def test_start_draw_four_is_replaced(players, monkeypatch):
    g = UnoGame(players)
    force_start(g, monkeypatch, card("Black", "Wild Draw Four", "Draw Four"),
                extra_card=card("Green", "4"))
    assert g.last_played["effect"] != "Draw Four"
    assert all(len(p.hand) == 7 for p in players)


# ─────────── Replay structure and event correctness ───────────

def test_replay_top_level_structure(game):
    assert set(game.replay_logs) == {"setup", "turns", "result"}
    assert isinstance(game.replay_logs["setup"], dict)
    assert isinstance(game.replay_logs["turns"], list)
    assert isinstance(game.replay_logs["result"], dict)


def test_setup_snapshot_is_not_modified_after_draw(players, monkeypatch):
    g = UnoGame(players)
    force_start(g, monkeypatch, card("Red", "5"))
    before = copy.deepcopy(g.replay_logs["setup"]["players"])
    g.deck.append(card("Green", "8"))
    g.draw_card()
    assert g.replay_logs["setup"]["players"] == before


def test_setup_event_initial_wild_color(players, monkeypatch):
    g = UnoGame(players)
    force_start(g, monkeypatch, card("Black", "Wild", "Wild"))
    events = g.replay_logs["setup"]["events"]
    assert any(e["type"] == "COLOR_CHANGE" and
               (e.get("color") or e.get("new_color")) == "Blue" for e in events)


def test_setup_draw_two_logged_with_exact_cards(players, monkeypatch):
    g = UnoGame(players)
    force_start(g, monkeypatch, card("Red", "Draw Two", "Draw Two"))
    events = g.replay_logs["setup"]["events"]
    draws = [e for e in events if e["type"] == "DRAW"]
    assert len(draws) == 1
    assert draws[0]["player"] == players[0].name
    assert isinstance(draws[0]["cards"], list)
    assert len(draws[0]["cards"]) == 2
    for c in draws[0]["cards"]:
        assert c in players[0].hand


def test_regular_play_event_has_one_card(game):
    game.current_player.hand = [card("Red", "8"), card("Blue", "1")]
    game.play_turn(1)
    turns = game.replay_logs["turns"]
    assert len(turns) == 1
    assert turns[0]["player"] == "P1"
    events = turns[0]["events"]
    play = [e for e in events if e["type"] == "PLAY"]
    assert len(play) == 1
    assert play[0]["player"] == "P1"
    assert play[0]["card"] == card("Red", "8")


def test_normal_draw_logged_as_list_of_one_card(game):
    game.current_player.hand = [card("Blue", "2")]
    game.deck = [card("Green", "8")]
    game.play_turn(0)
    events = game.replay_logs["turns"][-1]["events"]
    draws = [e for e in events if e["type"] == "DRAW"]
    assert len(draws) == 1
    assert draws[0]["player"] == "P1"
    assert draws[0]["cards"] == [card("Green", "8")]


@pytest.mark.parametrize("effect,count", [("Draw Two", 2), ("Draw Four", 4)])
def test_penalty_draw_log_contains_all_cards(game, players, monkeypatch, effect, count):
    if effect == "Draw Two":
        played = card("Red", "Draw Two", effect)
    else:
        played = card("Black", "Wild Draw Four", effect)
        monkeypatch.setattr(players[0].agent, "choose_action", lambda *a, **k: 2)
    game.current_player.hand = [played, card("Blue", "2")]
    game.deck = [card("Green", str(i)) for i in range(8)]
    game.play_turn(1)
    events = game.replay_logs["turns"][-1]["events"]
    draw_events = [e for e in events if e["type"] == "DRAW"]
    assert len(draw_events) == 1
    draw_event = draw_events[0]
    assert draw_event["player"] == "P2"
    assert len(draw_event["cards"]) == count
    assert all(c in players[1].hand for c in draw_event["cards"])


def test_reverse_event_has_explicit_new_direction(game):
    game.current_player.hand = [card("Red", "Reverse", "Reverse"), card("Blue", "2")]
    game.play_turn(1)
    events = game.replay_logs["turns"][-1]["events"]
    changes = [e for e in events if e["type"] == "DIRECTION_CHANGE"]
    assert len(changes) == 1
    assert changes[0]["direction"] == "counter_clockwise"


def test_wild_event_has_chosen_color(game, players, monkeypatch):
    monkeypatch.setattr(players[0].agent, "choose_action", lambda *a, **k: 2)
    game.current_player.hand = [card("Black", "Wild", "Wild"), card("Blue", "2")]
    game.play_turn(1)
    events = game.replay_logs["turns"][-1]["events"]
    changes = [e for e in events if e["type"] == "COLOR_CHANGE"]
    assert len(changes) == 1
    assert (changes[0].get("color") or changes[0].get("new_color")) == "Blue"


def test_followup_pass_recorded_by_correct_player(players, monkeypatch):
    g = UnoGame(players)
    force_start(g, monkeypatch, card("Red", "5"))
    # All P1 cards are Yellow 7; the drawn Red 8 is playable.
    g.deck = [card("Red", "8")]
    monkeypatch.setattr(players[0].agent, "choose_action",
                        lambda *a, **k: 0)
    # Run loop is controlled by a spy for just one turn.
    original_play_turn = g.play_turn
    observed = []
    def one_turn(choice=None):
        result = original_play_turn(choice)
        observed.append(result)
        # Avoid using run(): it intentionally calls setup_round() again.
        return result
    g.play_turn = one_turn
    assert g.play_turn(0) == "DRAWN_PLAYABLE"
    g.log_event({"type": "PASS", "player": g.current_player.name})
    g.next_player()
    assert g.replay_logs["turns"][-1]["events"][-1]["player"] == "P1"


def test_turn_events_can_be_serialized_as_strict_json(game):
    game.current_player.hand = [card("Red", "8"), card("Blue", "2")]
    game.play_turn(1)
    dumped = json.dumps(game.replay_logs, allow_nan=False)
    parsed = json.loads(dumped)
    assert parsed["turns"][0]["events"][0]["type"] == "PLAY"


def test_setup_json_has_no_nan(players, monkeypatch):
    g = UnoGame(players)
    force_start(g, monkeypatch, card("Red", "5"))
    json.dumps(g.replay_logs, allow_nan=False)


def test_setup_hands_match_game(players, monkeypatch):
    g = UnoGame(players)
    force_start(g, monkeypatch, card("Red", "5"))
    for p in players:
        assert g.replay_logs["setup"]["players"][p.name] == p.hand


def test_running_same_game_object_resets_log_state(players, monkeypatch):
    g = UnoGame(players)
    force_start(g, monkeypatch, card("Red", "5"))
    init_turn(g)
    assert len(g.replay_logs["turns"]) == 1
    force_start(g, monkeypatch, card("Blue", "3"))
    assert g.turn_count == 0
    assert g.replay_logs["turns"] == []
    assert g.last_played == card("Blue", "3")


# ─────────── End-to-end replay checks ───────────

def _run_simulated_game(seed):
    """Run without data.csv by substituting a realistic card supply."""
    rng = random.Random(seed)
    ps = [
        Player("P1", RandomAgent("R1")),
        Player("P2", HeuristicAgent("H2")),
        Player("P3", RandomAgent("R3")),
        Player("P4", HeuristicAgent("H4")),
    ]
    g = UnoGame(ps)
    # Build 108 card-like objects (same type distribution not required for replay).
    deck = []
    for color in COLORS:
        for n in range(10):
            deck.extend([card(color, str(n))] * 2)
        for e in ("Skip", "Reverse", "Draw Two"):
            deck.extend([card(color, e, e)] * 2)
    deck += [card("Black", "Wild", "Wild")] * 4
    deck += [card("Black", "Wild Draw Four", "Draw Four")] * 4
    rng.shuffle(deck)
    g.create_deck = lambda: setattr(g, "deck", [copy.deepcopy(x) for x in deck])
    g.shuffle_deck = lambda: None
    # Seeding module random keeps both agents deterministic within this test.
    random.seed(seed)
    original_play_turn = g.play_turn
    def guarded_play_turn(choice=None):
        if g.turn_count >= 1500:
            pytest.fail("Game exceeded 1500 turns: possible infinite loop / stalled state")
        return original_play_turn(choice)
    g.play_turn = guarded_play_turn
    g.run()
    return g


@pytest.mark.slow
@pytest.mark.parametrize("seed", [3, 7, 17, 29, 43])
def test_complete_game_terminates_and_logs_result(seed):
    g = _run_simulated_game(seed)
    assert not g.running
    assert g.winner in {p.name for p in g.players}
    assert g.replay_logs["result"]["Winner"] == g.winner
    assert g.replay_logs["result"]["Turns_count"] == g.turn_count
    assert len(g.replay_logs["turns"]) == g.turn_count
    json.dumps(g.replay_logs, allow_nan=False)


@pytest.mark.slow
@pytest.mark.parametrize("seed", [3, 7, 17])
def test_replay_reconstructs_final_hands(seed):
    """No UNO rules needed here: only PLAY removes, DRAW adds."""
    g = _run_simulated_game(seed)
    replay = g.replay_logs
    hands = copy.deepcopy(replay["setup"]["players"])

    def apply_event(event):
        kind = event["type"]
        if kind == "PLAY":
            player = event["player"]
            played = event["card"]
            assert played in hands[player], (
                f"Replay PLAY is impossible: {player} doesn't have {played}"
            )
            hands[player].remove(played)
        elif kind == "DRAW":
            cards = event["cards"]
            assert isinstance(cards, list), "DRAW.cards must always be a list"
            hands[event["player"]].extend(copy.deepcopy(cards))

    for event in replay["setup"].get("events", []):
        apply_event(event)
    for turn in replay["turns"]:
        for event in turn["events"]:
            apply_event(event)

    for player in g.players:
        assert Counter(map(str, hands[player.name])) == Counter(
            map(str, player.hand)
        ), f"Reconstructed hand differs for {player.name}"


@pytest.mark.slow
def test_replay_events_have_valid_structure():
    g = _run_simulated_game(23)
    known = {"PLAY", "DRAW", "PASS", "COLOR_CHANGE",
             "DIRECTION_CHANGE", "SKIP"}

    for turn_num, turn in enumerate(g.replay_logs["turns"], start=1):
        assert turn["turn"] == turn_num
        assert turn["player"] in {p.name for p in g.players}
        assert isinstance(turn["events"], list)
        for event in turn["events"]:
            assert event["type"] in known
            if event["type"] == "PLAY":
                assert "player" in event and "card" in event
                assert set(event["card"]) >= {"color", "value", "effect"}
            elif event["type"] == "DRAW":
                assert "player" in event
                assert isinstance(event["cards"], list)
                assert all(set(c) >= {"color", "value", "effect"} for c in event["cards"])


@pytest.mark.slow
def test_more_game_runs_have_no_missing_actions():
    for seed in range(10):
        g = _run_simulated_game(seed + 100)
        assert not g.running
        assert g.turn_count > 0
        assert g.replay_logs["turns"]
