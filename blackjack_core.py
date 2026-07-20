"""Ядро модуля «Блэкджек»: логика игры без импорта discord.

Без импорта discord — юнит-тестируемо напрямую (подход casino_core.py).
Настройки (min_bet, max_bet, house_edge_percent) берутся из casino_core —
блэкджек является третьей игрой казино и не хранит отдельный конфиг.

Жизненный цикл партии:
    game = new_game(bet)        # сдача карт
    hit(game)                   # добавить карту игроку (повторять)
    dealer_play(game)           # дилер разыгрывает (после stand/double)
    result = resolve(game)      # определить итог
    prize = payout(bet, result, house_edge_percent)
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum


# ──────────────────────────── Колода ────────────────────────────

SUITS = ("♠", "♥", "♦", "♣")
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")

# Туз отображается как «A», валет/дама/король — три отдельных символа.
_RANK_VALUES: dict[str, int] = {
    "A": 11,  # умный подсчёт: 11 пока не перебор, потом 1
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10,
}

# Эмодзи-масти для красивого embed-а (используются в blackjack.py)
SUIT_EMOJI = {"♠": "♠️", "♥": "♥️", "♦": "♦️", "♣": "♣️"}

DEALER_STAND_THRESHOLD = 17  # дилер стоит при 17 и выше


def _build_deck() -> list[str]:
    """Одна стандартная колода из 52 карт в формате «ранг+масть», например «A♠»."""
    return [f"{rank}{suit}" for suit in SUITS for rank in RANKS]


def _shuffled_deck() -> list[str]:
    deck = _build_deck()
    random.shuffle(deck)
    return deck


# ──────────────────────────── Подсчёт очков ────────────────────────────

def card_rank(card: str) -> str:
    """Ранг карты: «10♦» → «10», «A♠» → «A»."""
    return card[:-1]  # всё кроме последнего символа (масти)


def card_suit(card: str) -> str:
    """Масть карты: «10♦» → «♦», «A♠» → «♠»."""
    return card[-1]


def hand_value(hand: list[str]) -> int:
    """Сумма очков руки.

    Тузы умные: каждый туз считается как 11, если итог ≤ 21, иначе как 1.
    При нескольких тузах каждый проверяется отдельно.
    """
    total = 0
    aces = 0
    for card in hand:
        rank = card_rank(card)
        val = _RANK_VALUES[rank]
        if rank == "A":
            aces += 1
        total += val
    # Понижаем тузы с 11 до 1 пока не выйдем из перебора
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def is_bust(hand: list[str]) -> bool:
    return hand_value(hand) > 21


def is_blackjack(hand: list[str]) -> bool:
    """Натуральный блэкджек: ровно 2 карты и 21 очко."""
    return len(hand) == 2 and hand_value(hand) == 21


def can_double(hand: list[str]) -> bool:
    """Удвоение возможно только на первой паре (2 карты)."""
    return len(hand) == 2


# ──────────────────────────── Структура партии ────────────────────────────

class GameResult(Enum):
    BLACKJACK = "blackjack"  # натуральный BJ у игрока (×2.5)
    WIN       = "win"        # обычная победа (×2)
    PUSH      = "push"       # ничья (возврат ставки)
    LOSE      = "lose"       # проигрыш (0)


@dataclass
class BlackjackGame:
    deck:     list[str]        # оставшиеся карты (вершина = последний элемент)
    player:   list[str]        # рука игрока
    dealer:   list[str]        # рука дилера
    bet:      int              # исходная ставка (до double down)
    doubled:  bool = False     # был ли Double Down
    finished: bool = False     # партия завершена (нельзя ходить)
    result:   GameResult | None = None  # заполняется после dealer_play+resolve


# ──────────────────────────── Управление партией ────────────────────────────

def _deal_card(game: BlackjackGame) -> str:
    """Взять карту с вершины колоды."""
    return game.deck.pop()


def new_game(bet: int) -> BlackjackGame:
    """Создать новую партию: перетасовать колоду, сдать по 2 карты."""
    deck = _shuffled_deck()
    # Временно создаём с пустыми руками, затем сдаём
    game = BlackjackGame(deck=deck, player=[], dealer=[], bet=bet)
    # Сдача: игрок—дилер—игрок—дилер (классический порядок)
    game.player.append(_deal_card(game))
    game.dealer.append(_deal_card(game))
    game.player.append(_deal_card(game))
    game.dealer.append(_deal_card(game))
    return game


def hit(game: BlackjackGame) -> str:
    """Игрок берёт карту. Возвращает взятую карту."""
    card = _deal_card(game)
    game.player.append(card)
    return card


def dealer_play(game: BlackjackGame) -> None:
    """Дилер разыгрывает по правилу «стоит на 17+»."""
    while hand_value(game.dealer) < DEALER_STAND_THRESHOLD:
        game.dealer.append(_deal_card(game))


# ──────────────────────────── Итог и выплаты ────────────────────────────

def resolve(game: BlackjackGame) -> GameResult:
    """Определить итог партии (вызывать после dealer_play).

    Правила в порядке приоритета:
    1. Игрок bust → LOSE (даже если у дилера тоже bust).
    2. У игрока натуральный BJ, у дилера нет → BLACKJACK.
    3. Дилер bust → WIN.
    4. Сравнение очков: больше → WIN, равно → PUSH, меньше → LOSE.
    """
    pv = hand_value(game.player)
    dv = hand_value(game.dealer)

    if is_bust(game.player):
        return GameResult.LOSE

    if is_blackjack(game.player) and not is_blackjack(game.dealer):
        return GameResult.BLACKJACK

    if is_bust(game.dealer):
        return GameResult.WIN

    if pv > dv:
        return GameResult.WIN
    if pv == dv:
        return GameResult.PUSH
    return GameResult.LOSE


# Таблица множителей выплат (применяются к исходной ставке)
_RESULT_MULTIPLIERS: dict[GameResult, float] = {
    GameResult.BLACKJACK: 2.5,
    GameResult.WIN:       2.0,
    GameResult.PUSH:      1.0,  # возврат ставки
    GameResult.LOSE:      0.0,
}


def payout(bet: int, result: GameResult, house_edge_percent: int) -> int:
    """Сумма к зачислению на баланс (0 при проигрыше, возврат при ничье).

    При Double Down исходная ставка удвоена до вызова — передавать
    реальную потраченную ставку (bet * 2).

    house_edge_percent: аналогично casino_core — уменьшает выплату
    (не применяется к PUSH, чтобы ничья возвращала ровно ставку).
    """
    multiplier = _RESULT_MULTIPLIERS[result]
    raw = bet * multiplier
    if result == GameResult.PUSH:
        return int(raw)  # возврат без среза house_edge
    return int(raw * (100 - house_edge_percent) / 100)


# ──────────────────────────── Форматирование для embed ────────────────────────────

def format_hand(hand: list[str], hide_first: bool = False) -> str:
    """Форматировать руку в строку для embed.

    hide_first=True — первая карта дилера скрыта («🂠»).
    Пример: «🂠 8♠» или «A♥ 7♦ 5♣».
    """
    if not hand:
        return "—"
    cards = list(hand)
    if hide_first:
        cards[0] = "🂠"
    return "  ".join(cards)


def format_value(hand: list[str], hide_first: bool = False) -> str:
    """Счёт для отображения; «?» когда первая карта скрыта."""
    if hide_first:
        # Показываем только счёт открытых карт
        visible = hand[1:]
        return f"{hand_value(visible)} + ?" if visible else "?"
    return str(hand_value(hand))
