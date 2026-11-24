from pokemon_ai.mechanics.type_chart import effectiveness


def test_type_effectiveness_and_missing_type():
    chart = {"fire": {"grass": 2, "water": 0.5}}
    assert effectiveness(chart, "fire", ["grass"]) == 2
    assert effectiveness(chart, "fire", ["water"]) == 0.5
    assert effectiveness(chart, "normal", ["ghost"]) == 1
