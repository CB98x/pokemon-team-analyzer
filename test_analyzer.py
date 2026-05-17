"""
test_analyzer.py — tests for the analyzer module.

Run with:  pytest -v
"""

import pytest
from unittest.mock import patch, Mock

from analyzer import fetch_pokemon, analyze_team, format_report



# ─── Tests for analyze_team ──────────────────────────────────────────────────
# We can test analyze_team without hitting the API — it's pure logic on dicts.

def make_fake_pokemon(name, types, hp=50, attack=50, defense=50, speed=50):
    """Helper to build fake Pokémon dicts. Reduces test boilerplate."""
    return {
        "name": name,
        "types": types,
        "stats": {"hp": hp, "attack": attack, "defense": defense, "speed": speed},
    }


def test_analyze_team_computes_averages():
    team = [
        make_fake_pokemon("a", ["fire"], hp=60),
        make_fake_pokemon("b", ["water"], hp=40),
        make_fake_pokemon("c", ["grass"], hp=50),
    ]
    result = analyze_team(team)
    assert result["average_stats"]["hp"] == 50.0
    assert result["team_size"] == 3


def test_analyze_team_collects_types():
    team = [
        make_fake_pokemon("a", ["fire", "flying"]),
        make_fake_pokemon("b", ["water"]),
        make_fake_pokemon("c", ["fire"]),     # duplicate fire — should dedupe
    ]
    result = analyze_team(team)
    assert set(result["types"]) == {"fire", "flying", "water"}


def test_analyze_team_rejects_too_small():
    team = [make_fake_pokemon("a", ["fire"]), make_fake_pokemon("b", ["water"])]
    # PYTHON BASIC: pytest.raises asserts that an exception IS raised.
    with pytest.raises(ValueError, match="3–6 Pokémon"):
        analyze_team(team)


def test_analyze_team_rejects_too_big():
    team = [make_fake_pokemon(f"p{i}", ["fire"]) for i in range(7)]
    with pytest.raises(ValueError):
        analyze_team(team)


def test_analyze_team_finds_weaknesses():
    # A pure-fire team should be weak to water, ground, rock.
    team = [make_fake_pokemon(f"p{i}", ["fire"]) for i in range(3)]
    result = analyze_team(team)
    assert "water" in result["weak_against"]
    assert "ground" in result["weak_against"]


# ─── Tests for fetch_pokemon ─────────────────────────────────────────────────
# Here we MOCK the network call so tests don't depend on the API being up.
# This is critical: real tests must be fast and reliable. Hitting a live API
# means your tests fail when the API is slow, even if your code is fine.

@patch("analyzer.requests.get")
def test_fetch_pokemon_success(mock_get):
    # Build a fake API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "pikachu",
        "types": [{"type": {"name": "electric"}}],
        "stats": [
            {"stat": {"name": "hp"}, "base_stat": 35},
            {"stat": {"name": "attack"}, "base_stat": 55},
        ],
    }
    mock_get.return_value = mock_response

    result = fetch_pokemon("pikachu")
    assert result["name"] == "pikachu"
    assert result["types"] == ["electric"]
    assert result["stats"]["hp"] == 35


@patch("analyzer.requests.get")
def test_fetch_pokemon_not_found(mock_get):
    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="not found"):
        fetch_pokemon("notarealpokemon")


# ─── Test for format_report ──────────────────────────────────────────────────

def test_format_report_includes_names():
    analysis = {
        "team_size": 3,
        "names": ["pikachu", "charizard", "blastoise"],
        "average_stats": {"hp": 60.0, "attack": 70.0, "defense": 65.0, "speed": 75.0},
        "types": ["electric", "fire", "water"],
        "weak_against": ["ground", "rock"],
    }
    output = format_report(analysis)
    assert "pikachu" in output
    assert "charizard" in output
    assert "TEAM ANALYSIS" in output
