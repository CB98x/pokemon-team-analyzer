"""
main.py — command-line entry point.

Run with:  python main.py pikachu charizard blastoise
"""

import logging
import sys

from analyzer import fetch_pokemon, analyze_team, format_report, get_metrics_snapshot

# Configure logging once, here at the entry point. NOT inside library code.
# This is a SWE convention: libraries get loggers, applications configure them.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

def main() -> int:
    # PYTHON BASIC: sys.argv is the list of command-line arguments.
    # sys.argv[0] is the script name, so the actual args start at [1:].
    pokemon_names = sys.argv[1:]

    if not pokemon_names:
        print("Usage: python main.py <pokemon1> <pokemon2> <pokemon3> [...]")
        print("Example: python main.py pikachu charizard blastoise venusaur")
        return 1        # non-zero exit code = error, a Unix convention

    logger.info("Starting team analysis for: %s", pokemon_names)

    # PYTHON BASIC: try/except to handle errors gracefully.
    try:
        team = []
        for name in pokemon_names:
            pokemon = fetch_pokemon(name)
            team.append(pokemon)

        analysis = analyze_team(team)
        report = format_report(analysis)
        print(report)

        # Print metrics — observability in action.
        snapshot = get_metrics_snapshot()
        print("\nMetrics:")
        print(f"  API calls:       {snapshot['api_calls_total']}")
        print(f"  API failures:    {snapshot['api_calls_failed']}")
        print(f"  Avg latency:     {snapshot['avg_latency_ms']} ms")
        print(f"  Teams analyzed:  {snapshot['teams_analyzed']}")
        return 0

    except ValueError as e:
        # User input error (bad Pokémon name, wrong team size)
        logger.error("Input error: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        # Anything else — network error, unexpected response, etc.
        logger.exception("Unexpected error")
        print(f"Something went wrong: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    # PYTHON BASIC: this idiom means "only run main() if this file is the
    # entry point, not if it's imported by another file." Standard practice.
    sys.exit(main())    

