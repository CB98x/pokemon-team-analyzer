"""
analyzer.py — core logic for the Pokémon Team Analyzer.

Has three responsibilities:
  1. Fetch one Pokémon from the API
  2. Analyze a list of Pokémon
  3. Format the analysis as a string

Note: no printing in this file. Printing is the CLI's job (main.py).
This separation makes the logic testable.
"""

import logging              # Python's built-in logging library
import time                 # for timing API calls (observability)
import requests             # the HTTP library we installed

# ─── Logging setup ──────────────────────────────────────────────────────────
# Logging is like print(), but better. It has levels (DEBUG/INFO/WARNING/ERROR),
# can be turned on/off without changing code, and goes to files in production.
# As a SWE, you use logger.info() instead of print() for anything important.
logger = logging.getLogger(__name__)

# ─── Constants ──────────────────────────────────────────────────────────────
# PYTHON BASIC: variables. ALL_CAPS by convention means "constant — don't change me."
POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/pokemon"
REQUEST_TIMEOUT_SECONDS = 5     # never let a single API call hang forever
MIN_TEAM_SIZE = 3
MAX_TEAM_SIZE = 6

# ─── Observability: simple in-memory metrics ────────────────────────────────
# In a real production service, these would go to a system like CloudWatch,
# Datadog, or Prometheus. Here we just keep counters in a dict to demonstrate
# the concept. We track FOUR metrics — that's the limit your dad set.
# PYTHON BASIC: dictionary (a key→value mapping).
metrics = {
    "api_calls_total": 0,           # how many requests we sent
    "api_calls_failed": 0,          # how many of those failed
    "api_latency_ms_total": 0,      # cumulative latency, for averaging
    "teams_analyzed": 0            # how many full teams we processed
}


# ─── Function 1: fetch one Pokémon ──────────────────────────────────────────
def fetch_pokemon(name: str) -> dict:
    """
    Fetch a single Pokémon from PokéAPI and return only the fields we care about.

    Returns a dict like:
        {"name": "pikachu", "types": ["electric"], "stats": {"hp": 35, ...}}

    Raises:
        ValueError: if the Pokémon doesn't exist (404)
        requests.RequestException: if the network fails
    """
    # PYTHON BASIC: f-string for string formatting. Cleaner than concatenation.
    url = f"{POKEAPI_BASE_URL}/{name.lower()}"
    logger.info("Fetching Pokémon: %s", name)

    # Time the API call so we can record latency. Observability!
    start = time.time()
    metrics["api_calls_total"] += 1     # PYTHON BASIC: += increments by 1

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as e:
        # Catching network errors. Always handle the unhappy path.
        metrics["api_calls_failed"] += 1
        logger.error("Network error fetching %s: %s", name, e)
        raise   # re-raise so the caller knows something went wrong

    latency_ms = (time.time() - start) * 1000
    metrics["api_latency_ms_total"] += latency_ms
    logger.debug("API call to %s took %.0f ms", name, latency_ms)

    # PYTHON BASIC: conditional (if-statement)
    if response.status_code == 404:
        metrics["api_calls_failed"] += 1
        logger.warning("Pokémon not found: %s", name)
        raise ValueError(f"Pokémon '{name}' not found")

    if response.status_code != 200:
        metrics["api_calls_failed"] += 1
        logger.error("Unexpected status %d for %s", response.status_code, name)
        raise RuntimeError(f"PokéAPI returned status {response.status_code}")

    # response.json() parses the JSON response into a Python dict.
    data = response.json()

    # The API gives us a HUGE response. Slim it down to what we need.
    # PYTHON BASIC: list comprehension. [x for x in y] builds a new list.
    types = [t["type"]["name"] for t in data["types"]]

    # PYTHON BASIC: dict comprehension. Same idea but for dicts.
    stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}

    return {
        "name": data["name"],
        "types": types,
        "stats": stats
    }

# ─── Type effectiveness data (for weakness analysis) ────────────────────────
# Mapping: attacker_type → list of types it's strong against.
# Simplified — real Pokémon has 18 types and a full chart. This is enough
# for our analyzer to give meaningful output without us hand-typing the
# whole 18×18 chart. In a real product, you'd fetch this from the API too.
TYPE_WEAKNESSES = {
    "fire":     ["water", "ground", "rock"],
    "water":    ["electric", "grass"],
    "grass":    ["fire", "ice", "poison", "flying", "bug"],
    "electric": ["ground"],
    "ice":      ["fire", "fighting", "rock", "steel"],
    "fighting": ["flying", "psychic", "fairy"],
    "poison":   ["ground", "psychic"],
    "ground":   ["water", "grass", "ice"],
    "flying":   ["electric", "ice", "rock"],
    "psychic":  ["bug", "ghost", "dark"],
    "bug":      ["fire", "flying", "rock"],
    "rock":     ["water", "grass", "fighting", "ground", "steel"],
    "ghost":    ["ghost", "dark"],
    "dragon":   ["ice", "dragon", "fairy"],
    "dark":     ["fighting", "bug", "fairy"],
    "steel":    ["fire", "fighting", "ground"],
    "fairy":    ["poison", "steel"],
    "normal":   ["fighting"],
}



# ─── Function 2: analyze a team ─────────────────────────────────────────────
def analyze_team(team: list) -> dict:
    """
    Given a list of Pokémon dicts (from fetch_pokemon), compute team stats.

    Returns a dict with average stats, type list, and weaknesses.
    """
    # PYTHON BASIC: validation. Fail fast and loud on bad input.
    if not (MIN_TEAM_SIZE <= len(team) <= MAX_TEAM_SIZE):
        raise ValueError(
            f"Team must have {MIN_TEAM_SIZE}–{MAX_TEAM_SIZE} Pokémon, got {len(team)}"
        )

    logger.info("Analyzing team of %d Pokémon", len(team))

    # PYTHON BASIC: building up totals with a loop.
    stat_totals = {"hp": 0, "attack": 0, "defense": 0, "speed": 0}
    all_types = []          # PYTHON BASIC: list — ordered, allows duplicates
    weaknesses = set()      # PYTHON BASIC: set — unordered, no duplicates

    # PYTHON BASIC: for-loop iterating through a list of dicts
    for pokemon in team:
        for stat_name in stat_totals:
            stat_totals[stat_name] += pokemon["stats"].get(stat_name, 0)

        # PYTHON BASIC: extending a list with another list
        all_types.extend(pokemon["types"])

        # Build up the set of weaknesses across the whole team
        for ptype in pokemon["types"]:
            for weakness in TYPE_WEAKNESSES.get(ptype, []):
                weaknesses.add(weakness)

    # Compute averages. PYTHON BASIC: dict comprehension again.
    averages = {name: round(total / len(team), 1) for name, total in stat_totals.items()}

    metrics["teams_analyzed"] += 1
    logger.info("Team analysis complete: %d unique types, %d weaknesses",
                len(set(all_types)), len(weaknesses))

    return {
        "team_size": len(team),
        "names": [p["name"] for p in team],
        "average_stats": averages,
        "types": sorted(set(all_types)),    # PYTHON BASIC: sorted() returns a list
        "weak_against": sorted(weaknesses),
    }


# ─── Function 3: format the report ──────────────────────────────────────────
def format_report(analysis: dict) -> str:
    """Convert an analysis dict into a human-readable string."""
    # PYTHON BASIC: building a string with a list and join — faster than +=
    lines = []
    lines.append("─" * 50)
    lines.append(f"  TEAM ANALYSIS — {analysis['team_size']} Pokémon")
    lines.append("─" * 50)
    lines.append(f"  Roster:       {', '.join(analysis['names'])}")
    lines.append(f"  Types:        {', '.join(analysis['types'])}")
    lines.append("")
    lines.append("  Average stats:")
    for stat, value in analysis["average_stats"].items():
        # PYTHON BASIC: f-string with formatting — :>8 right-pads to 8 chars
        lines.append(f"    {stat:>10}: {value}")
    lines.append("")
    lines.append(f"  Weak against: {', '.join(analysis['weak_against'])}")
    lines.append("─" * 50)
    return "\n".join(lines)


def get_metrics_snapshot() -> dict:
    """Return a copy of the metrics. Used by the CLI to print stats at the end."""
    snapshot = dict(metrics)        # PYTHON BASIC: making a copy of a dict
    if snapshot["api_calls_total"] > 0:
        snapshot["avg_latency_ms"] = round(
            snapshot["api_latency_ms_total"] / snapshot["api_calls_total"], 1
        )
    else:
        snapshot["avg_latency_ms"] = 0
    return snapshot
# ---

