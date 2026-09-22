import pytest

from player import Player
from game import UnoGame


# ============================================================
# Helpers / fixtures
# ============================================================

def card(color, value, effect="None"):
    """Small helper to create cards without repeating dictionaries everywhere."""
    return {
        "color": color,
        "value": value,
        "effect": effect,
    }


@pytest.fixture
def players():
    return [
        Player("P1"),
        Player("P2"),
        Player("P3"),
        Player("P4"),
    ]


@pytest.fixture
def game(players):
    """
    Basic deterministic game state:
    - P1 is playing
    - last card = Red 5
    - current color = Red
    """
    game = UnoGame(players)
    game.current_player = players[0]
    game.last_played = card("Red", "5")
    game.current_color = "Red"
    game.used = [game.last_played]
    return game


# ============================================================
# Player
# ============================================================

def test_player_starts_with_empty_hand():
    player = Player("P1")

    assert player.name == "P1"
    assert player.hand == []
    assert player.hand_size() == 0
    assert player.has_won() is True


def test_player_add_and_remove_card():
    player = Player("P1")
    c = card("Red", "7")

    player.add_card(c)

    assert player.hand_size() == 1
    assert c in player.hand
    assert player.has_won() is False

    player.remove_card(c)

    assert player.hand == []
    assert player.has_won() is True


# ============================================================
# legal_cards()
# ============================================================

def test_same_color_is_legal(game):
    c = card("Red", "9")
    game.current_player.hand = [c]

    assert c in game.legal_cards()


def test_same_value_is_legal(game):
    c = card("Blue", "5")
    game.current_player.hand = [c]

    assert c in game.legal_cards()


def test_black_card_is_always_legal(game):
    c = card("Black", "Wild", "Wild")
    game.current_player.hand = [c]

    assert c in game.legal_cards()


def test_wrong_color_and_wrong_value_is_illegal(game):
    c = card("Blue", "9")
    game.current_player.hand = [c]

    assert c not in game.legal_cards()


def test_legal_cards_uses_current_color_after_wild(game):
    """
    Important:
    after a Wild, last_played can still be Black,
    but the active color must be current_color.
    """
    game.last_played = card("Black", "Wild", "Wild")
    game.current_color = "Blue"

    blue = card("Blue", "8")
    red = card("Red", "2")

    game.current_player.hand = [blue, red]

    legal = game.legal_cards()

    assert blue in legal
    assert red not in legal


def test_legal_cards_does_not_modify_hand(game):
    hand = [
        card("Red", "9"),
        card("Blue", "9"),
        card("Black", "Wild", "Wild"),
    ]
    game.current_player.hand = hand.copy()

    game.legal_cards()

    assert game.current_player.hand == hand


# ============================================================
# next_player()
# ============================================================

def test_next_player_normal_order(game, players):
    game.current_player = players[0]

    game.next_player()

    assert game.current_player == players[1]


def test_next_player_wraps_from_last_to_first(game, players):
    game.current_player = players[3]

    game.next_player()

    assert game.current_player == players[0]


def test_next_player_reverse_order(game, players):
    game.current_player = players[0]
    game.normal_order = False

    game.next_player()

    assert game.current_player == players[3]


def test_next_player_reverse_from_middle(game, players):
    game.current_player = players[2]
    game.normal_order = False

    game.next_player()

    assert game.current_player == players[1]


def test_next_player_many_times_never_leaves_players(game, players):
    game.current_player = players[0]

    for _ in range(1000):
        game.next_player()

    assert game.current_player in players


def test_next_player_many_times_reverse_never_leaves_players(game, players):
    game.current_player = players[0]
    game.normal_order = False

    for _ in range(1000):
        game.next_player()

    assert game.current_player in players


# ============================================================
# play_card()
# ============================================================

def test_play_legal_card_updates_game_state(game):
    c = card("Red", "8")
    game.current_player.hand = [c]

    result = game.play_card(1)

    assert result is True
    assert c not in game.current_player.hand
    assert game.last_played == c
    assert game.used[-1] == c
    assert game.current_color == "Red"


def test_play_illegal_card_changes_nothing(game):
    illegal = card("Blue", "9")
    old_last = game.last_played
    old_color = game.current_color
    old_used = game.used.copy()

    game.current_player.hand = [illegal]

    result = game.play_card(1)

    assert result is False
    assert game.current_player.hand == [illegal]
    assert game.last_played == old_last
    assert game.current_color == old_color
    assert game.used == old_used


def test_player_wins_when_playing_last_card(game, players):
    c = card("Red", "8")
    game.current_player = players[0]
    game.current_player.hand = [c]

    game.play_card(1)

    assert game.running is False
    assert game.winner == players[0]
    assert players[0].hand == []


@pytest.mark.parametrize("special_card", [
    card("Red", "Skip", "Skip"),
    card("Red", "Reverse", "Reverse"),
    card("Red", "Draw Two", "Draw Two"),
])
def test_player_can_win_with_special_card_as_last_card(game, players, special_card):
    game.current_player = players[0]
    game.current_player.hand = [special_card]

    result = game.play_card(1)

    assert result is True
    assert game.running is False
    assert game.winner == players[0]


# ============================================================
# Invalid play_card() inputs
#
# These tests are intentionally strict.
# If they fail, harden play_card() so it returns False instead
# of raising TypeError / IndexError.
# ============================================================

@pytest.mark.parametrize("choice", [
    0,
    -1,
    -100,
    999,
    "hello",
    1.5,
    None,
])
def test_play_card_rejects_invalid_choice_without_crashing(game, choice):
    game.current_player.hand = [
        card("Red", "7"),
        card("Blue", "5"),
    ]

    before = game.current_player.hand.copy()

    result = game.play_card(choice)

    assert result is False
    assert game.current_player.hand == before


def test_play_card_on_empty_hand_returns_false(game):
    game.current_player.hand = []

    result = game.play_card(1)

    assert result is False


# ============================================================
# draw_card()
# ============================================================

def test_draw_card_adds_exactly_one_card(game):
    drawn = card("Green", "3")
    game.deck = [drawn]

    before = len(game.current_player.hand)

    result = game.draw_card()

    assert result == drawn
    assert len(game.current_player.hand) == before + 1
    assert game.current_player.hand[-1] == drawn
    assert game.deck == []


def test_draw_with_empty_deck_recycles_discard_pile(game):
    old1 = card("Blue", "2")
    old2 = card("Green", "4")
    top = card("Red", "5")

    game.deck = []
    game.used = [old1, old2, top]

    before = len(game.current_player.hand)

    drawn = game.draw_card()

    assert len(game.current_player.hand) == before + 1
    assert drawn in [old1, old2]

    # The top discard card must stay on the table.
    assert game.used == [top]

    # Of the two recyclable cards, one was drawn and one remains in deck.
    assert len(game.deck) == 1


def test_recycled_deck_never_contains_current_top_card(game):
    old1 = card("Blue", "2")
    old2 = card("Yellow", "6")
    top = card("Red", "Skip", "Skip")

    game.deck = []
    game.used = [old1, old2, top]

    game.draw_card()

    assert top not in game.deck
    assert game.used == [top]


# ============================================================
# Effects
# ============================================================

def test_skip_skips_exactly_one_player(game, players):
    game.current_player = players[0]
    game.last_played = card("Red", "Skip", "Skip")

    game.apply_effect()   # P1 -> P2 (P2 is skipped)
    game.next_player()    # P2 -> P3

    assert game.current_player == players[2]


def test_skip_wraps_around_table(game, players):
    game.current_player = players[3]
    game.last_played = card("Red", "Skip", "Skip")

    game.apply_effect()   # P4 -> P1 skipped
    game.next_player()    # P1 -> P2

    assert game.current_player == players[1]


def test_reverse_changes_direction(game):
    game.normal_order = True
    game.last_played = card("Red", "Reverse", "Reverse")

    game.apply_effect()

    assert game.normal_order is False


def test_two_reverse_restore_original_direction(game):
    game.normal_order = True
    game.last_played = card("Red", "Reverse", "Reverse")

    game.apply_effect()
    game.apply_effect()

    assert game.normal_order is True


def test_draw_two_draws_exactly_two_cards(game, players):
    game.current_player = players[0]
    game.deck = [
        card("Yellow", "1"),
        card("Blue", "2"),
        card("Green", "3"),
    ]
    game.last_played = card("Red", "Draw Two", "Draw Two")

    game.apply_effect()

    assert game.current_player == players[1]
    assert len(players[1].hand) == 2
    assert len(game.deck) == 1


def test_draw_two_skips_penalized_player_after_normal_next_player(game, players):
    game.current_player = players[0]
    game.deck = [
        card("Yellow", "1"),
        card("Blue", "2"),
        card("Green", "3"),
    ]
    game.last_played = card("Red", "Draw Two", "Draw Two")

    game.apply_effect()   # P2 draws two
    game.next_player()    # P2 is skipped

    assert game.current_player == players[2]


def test_wild_changes_current_color(game, monkeypatch):
    game.last_played = card("Black", "Wild", "Wild")

    monkeypatch.setattr("builtins.input", lambda _: "2")

    game.apply_effect()

    assert game.current_color == "Blue"


@pytest.mark.parametrize(
    "choice, expected_color",
    [
        ("1", "Red"),
        ("2", "Blue"),
        ("3", "Yellow"),
        ("4", "Green"),
    ],
)
def test_wild_accepts_all_four_colors(game, monkeypatch, choice, expected_color):
    game.last_played = card("Black", "Wild", "Wild")

    monkeypatch.setattr("builtins.input", lambda _: choice)

    game.apply_effect()

    assert game.current_color == expected_color


def test_draw_four_draws_exactly_four_cards(game, players, monkeypatch):
    game.current_player = players[0]
    game.deck = [
        card("Red", "1"),
        card("Blue", "2"),
        card("Green", "3"),
        card("Yellow", "4"),
        card("Red", "5"),
    ]
    game.last_played = card("Black", "Wild Draw Four", "Draw Four")

    monkeypatch.setattr("builtins.input", lambda _: "3")

    game.apply_effect()

    assert game.current_color == "Yellow"
    assert game.current_player == players[1]
    assert len(players[1].hand) == 4
    assert len(game.deck) == 1


def test_draw_four_penalized_player_is_skipped_after_normal_next_player(
    game, players, monkeypatch
):
    game.current_player = players[0]
    game.deck = [
        card("Red", "1"),
        card("Blue", "2"),
        card("Green", "3"),
        card("Yellow", "4"),
        card("Red", "5"),
    ]
    game.last_played = card("Black", "Wild Draw Four", "Draw Four")

    monkeypatch.setattr("builtins.input", lambda _: "1")

    game.apply_effect()   # P2 draws four
    game.next_player()    # P2 skipped

    assert game.current_player == players[2]


# ============================================================
# play_turn()
# ============================================================

def test_successful_play_turn_advances_to_next_player(game, players):
    game.current_player = players[0]
    game.current_player.hand = [
        card("Red", "8"),
        card("Blue", "9"),
    ]

    result = game.play_turn(1)

    assert result is True
    assert game.current_player == players[1]


def test_illegal_play_turn_does_not_advance_player(game, players):
    game.current_player = players[0]
    game.current_player.hand = [
        card("Blue", "9"),
        card("Green", "2"),
    ]

    result = game.play_turn(1)

    assert result is False
    assert game.current_player == players[0]


def test_draw_non_playable_card_ends_turn(game, players):
    game.current_player = players[0]

    # Current state: Red 5
    game.deck = [
        card("Green", "9")  # not Red, not value 5, not Black
    ]

    result = game.play_turn()

    assert result is None
    assert card("Green", "9") in players[0].hand
    assert game.current_player == players[1]


def test_draw_playable_card_does_not_crash_and_keeps_decision_with_same_player(
    game, players
):
    """
    Desired behaviour:
    If a drawn card is playable, the player/agent should get a second decision:
    play the drawn card OR pass.

    This test will expose the current implementation if play_turn()
    sends the card dictionary into play_card() instead of a card index.
    """
    game.current_player = players[0]
    drawn = card("Red", "9")
    game.deck = [drawn]

    game.play_turn()

    assert drawn in players[0].hand
    assert game.current_player == players[0]


# ============================================================
# Winner / game state
# ============================================================

def test_check_winner_false_when_player_has_cards(game):
    game.current_player.hand = [card("Red", "8")]

    result = game.check_winner()

    assert result is False
    assert game.running is True
    assert game.winner is None


def test_check_winner_true_when_hand_is_empty(game, players):
    game.current_player = players[0]
    game.current_player.hand = []

    result = game.check_winner()

    assert result is True
    assert game.running is False
    assert game.winner == players[0]


def test_winner_reference_remains_correct_even_if_current_player_changes(game, players):
    game.current_player = players[0]
    game.current_player.hand = []

    game.check_winner()
    game.next_player()

    assert game.current_player == players[1]
    assert game.winner == players[0]


# ============================================================
# Reset
# ============================================================

def test_reset_hand_clears_every_player(game, players):
    for player in players:
        player.hand = [
            card("Red", "1"),
            card("Blue", "2"),
        ]

    game.reset_hand()

    assert all(player.hand == [] for player in players)
