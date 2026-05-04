# Pokémon Team Analyzer

A command-line tool that analyzes a team of 3–6 Pokémon and reports on their
combined stats, type coverage, and defensive weaknesses. Built as a
learning project to practice consuming a public REST API.


### Note(5/3/26) - This project is still in Progress!

## Demo

```
$ python main.py pikachu charizard blastoise venusaur

──────────────────────────────────────────────────
  TEAM ANALYSIS — 4 Pokémon
──────────────────────────────────────────────────
  Roster:       pikachu, charizard, blastoise, venusaur
  Types:        electric, fire, flying, grass, poison, water

  Average stats:
            hp: 76.2
        attack: 78.5
       defense: 72.0
         speed: 87.5

  Weak against: electric, flying, ground, ice, psychic, rock
──────────────────────────────────────────────────

Metrics:
  API calls:       4
  API failures:    0
  Avg latency:     142.3 ms
  Teams analyzed:  1
```

## Setup

```bash
git clone https://github.com/<your-username>/pokemon-team-analyzer.git
cd pokemon-team-analyzer
python3 -m venv venv
source venv/bin/activate              # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python main.py <pokemon1> <pokemon2> <pokemon3> [...up to 6]
```

Examples:

```bash
python main.py pikachu charizard blastoise
python main.py mewtwo lugia rayquaza dialga arceus
```

## Running tests

```bash
pytest -v
```

## Project structure

```
.
├── analyzer.py          Core logic (API client, team analysis, formatting)
├── main.py              CLI entry point
├── test_analyzer.py     Unit tests (with mocked HTTP calls)
├── requirements.txt     Pinned dependencies
└── README.md            This file
```

## Architecture notes

- **Separation of concerns:** `analyzer.py` has no I/O — it's pure logic and
  HTTP calls. `main.py` handles user input and printing. This makes the
  analyzer trivially testable.
- **Logging:** uses Python's `logging` module. Configured once in `main.py`,
  used everywhere via module loggers.
- **Observability:** four in-memory metrics (`api_calls_total`,
  `api_calls_failed`, `api_latency_ms_total`, `teams_analyzed`). In a
  production system these would be exported to CloudWatch / Datadog /
  Prometheus.
- **Error handling:** distinguishes user errors (bad Pokémon name → exit 1)
  from system errors (network failure → exit 2).

## Data source

Type and stat data from [PokéAPI](https://pokeapi.co/), a free public
REST API. No authentication required.

## License

MIT