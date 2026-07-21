"""Тесты ядра блэкджека: очки руки, ход дилера, итоги, выплаты, форматирование."""

import pytest

import blackjack_core as bj


# ────────────────────────── Очки руки ──────────────────────────

@pytest.mark.parametrize("hand, expected", [
    (["2♠", "3♦"], 5),
    (["10♠", "J♦"], 20),
    (["A♠", "K♦"], 21),          # туз как 11
    (["A♠", "A♦"], 12),          # второй туз понижен до 1
    (["A♠", "A♦", "9♣"], 21),    # 11 + 1 + 9
    (["A♠", "K♦", "5♣"], 16),    # туз понижен: 1 + 10 + 5
    (["K♠", "Q♦", "5♣"], 25),    # перебор
])
def test_hand_value(hand, expected):
    assert bj.hand_value(hand) == expected


def test_is_bust():
    assert bj.is_bust(["K♠", "Q♦", "5♣"]) is True
    assert bj.is_bust(["A♠", "K♦"]) is False


def test_is_blackjack_only_two_cards():
    assert bj.is_blackjack(["A♠", "K♦"]) is True
    assert bj.is_blackjack(["7♠", "7♦", "7♣"]) is False  # 21, но 3 карты
    assert bj.is_blackjack(["10♠", "9♦"]) is False


def test_can_double_only_on_first_pair():
    assert bj.can_double(["5♠", "6♦"]) is True
    assert bj.can_double(["5♠", "6♦", "2♣"]) is False


def test_card_rank_and_suit():
    assert bj.card_rank("10♦") == "10"
    assert bj.card_suit("10♦") == "♦"
    assert bj.card_rank("A♠") == "A"


# ────────────────────────── Партия ──────────────────────────

def test_new_game_deals_two_cards_each():
    game = bj.new_game(100)
    assert len(game.player) == 2
    assert len(game.dealer) == 2
    assert len(game.deck) == 48
    assert game.bet == 100
    assert game.finished is False


def test_hit_takes_top_card():
    game = bj.BlackjackGame(deck=["2♠", "5♣"], player=["10♠", "9♦"], dealer=[], bet=10)
    card = bj.hit(game)
    assert card == "5♣"  # вершина колоды — последний элемент
    assert game.player == ["10♠", "9♦", "5♣"]


def test_dealer_stands_on_17():
    game = bj.BlackjackGame(deck=["2♠"], player=[], dealer=["10♣", "7♥"], bet=10)
    bj.dealer_play(game)
    assert game.dealer == ["10♣", "7♥"]  # 17 — не берёт


def test_dealer_draws_under_17():
    game = bj.BlackjackGame(deck=["5♠", "2♦"], player=[], dealer=["10♣", "4♥"], bet=10)
    bj.dealer_play(game)
    # 14 → берёт 2♦ (16) → берёт 5♠ (21) → стоит
    assert game.dealer == ["10♣", "4♥", "2♦", "5♠"]


# ────────────────────────── Итоги ──────────────────────────

def _game(player, dealer):
    return bj.BlackjackGame(deck=[], player=player, dealer=dealer, bet=100)


def test_resolve_player_bust_loses_even_if_dealer_busts():
    assert bj.resolve(_game(["K♠", "Q♦", "5♣"], ["K♥", "Q♣", "5♦"])) is bj.GameResult.LOSE


def test_resolve_natural_blackjack():
    assert bj.resolve(_game(["A♠", "K♦"], ["10♣", "9♥"])) is bj.GameResult.BLACKJACK


def test_resolve_both_naturals_push():
    assert bj.resolve(_game(["A♠", "K♦"], ["A♥", "Q♣"])) is bj.GameResult.PUSH


def test_resolve_dealer_bust_wins():
    assert bj.resolve(_game(["10♠", "9♦"], ["K♥", "Q♣", "5♦"])) is bj.GameResult.WIN


def test_resolve_compare_values():
    assert bj.resolve(_game(["10♠", "9♦"], ["10♥", "8♣"])) is bj.GameResult.WIN
    assert bj.resolve(_game(["10♠", "8♦"], ["10♥", "8♣"])) is bj.GameResult.PUSH
    assert bj.resolve(_game(["10♠", "7♦"], ["10♥", "8♣"])) is bj.GameResult.LOSE


def test_twenty_one_from_three_cards_beats_dealer_twenty():
    assert bj.resolve(_game(["7♠", "7♦", "7♣"], ["10♥", "Q♣"])) is bj.GameResult.WIN


# ────────────────────────── Выплаты ──────────────────────────

def test_payout_multipliers_no_edge():
    assert bj.payout(100, bj.GameResult.BLACKJACK, 0) == 250
    assert bj.payout(100, bj.GameResult.WIN, 0) == 200
    assert bj.payout(100, bj.GameResult.PUSH, 0) == 100
    assert bj.payout(100, bj.GameResult.LOSE, 0) == 0


def test_payout_house_edge_reduces_win_but_not_push():
    assert bj.payout(100, bj.GameResult.WIN, 10) == 180
    assert bj.payout(100, bj.GameResult.BLACKJACK, 10) == 225
    assert bj.payout(100, bj.GameResult.PUSH, 10) == 100  # ничья возвращает ровно ставку


# ────────────────────────── Форматирование ──────────────────────────

def test_format_hand_hides_first_card():
    assert bj.format_hand(["10♣", "8♠"], hide_first=True) == "🂠  8♠"
    assert bj.format_hand(["A♥", "7♦", "5♣"]) == "A♥  7♦  5♣"
    assert bj.format_hand([]) == "—"


def test_format_value_hides_hole_card():
    assert bj.format_value(["10♣", "8♠"], hide_first=True) == "8 + ?"
    assert bj.format_value(["10♣", "8♠"]) == "18"
