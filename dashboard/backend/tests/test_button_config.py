"""Тесты per-guild персистентности конфигов кнопок-форм (button.py, Фаза 2.2б).

Раньше load читал плоский buttons_config.json, а save писал в settings_db — рассинхрон
плюс отсутствующий импорт settings_db (NameError). Здесь фиксируем корректный round-trip
через settings_db с изоляцией по гильдиям.
"""

import bot.modules.utility.button as button


def test_load_returns_defaults_when_empty():
    data = button._load_buttons_config(1)
    assert data == {"forms": {}, "next_form_id": 1}


def test_save_and_load_round_trip():
    config = button._load_buttons_config(1)
    config["forms"]["1"] = {"button_name": "Заявка", "questions": ["Ник?"]}
    config["next_form_id"] = 2
    button._save_buttons_config(1, config)

    loaded = button._load_buttons_config(1)
    assert loaded["forms"]["1"]["button_name"] == "Заявка"
    assert loaded["next_form_id"] == 2


def test_configs_are_scoped_per_guild():
    config = button._load_buttons_config(1)
    config["forms"]["1"] = {"button_name": "A", "questions": ["q"]}
    button._save_buttons_config(1, config)

    # другой сервер не видит форм первого
    assert button._load_buttons_config(2)["forms"] == {}
