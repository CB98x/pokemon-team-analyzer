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
