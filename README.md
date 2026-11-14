# IoT Telemetry Simulator

A deterministic Python command-line tool for generating hierarchical sensor telemetry. Configuration expands device groups into sensor paths; each sensor emits a bounded random, cycling gauge, or stepped counter value.

## Run

Python 3.10 or later is sufficient. The simulator uses only the standard library.

```sh
python3 simulator.py --config config.txt --steps 100 --seed 42 --output telemetry.jsonl
python3 simulator.py --config config.txt --steps 10 --format csv --output telemetry.csv
python3 -m unittest discover -s tests -v
```

`new.py` remains a compatibility entry point. The default configuration is resolved relative to the script, so commands work from another working directory as well.

## Configuration

```text
Building(2)/Floor(3)/Temperature Random#18,25
Building(2)/Power Counter#0,100,5
Building(2)/Status Gauge#0,3
```

`Name(N)` creates N instances. Unnumbered names create one instance. Each expanded path must be unique. The default limit is 100,000 sensors; oversized or malformed configurations fail with a line number before generation.

| Generator | Behavior |
|---|---|
| `Random#min,max` | Seeded integer draw, inclusive bounds |
| `Gauge#min,max` | Starts at min, increments by one, wraps to min |
| `Counter#min,max,step` | Starts at min, increments by positive step, wraps to min |

Rows contain `path`, `timestamp`, and `value`. Timestamps are Unix seconds. They start at 0 by default for reproducible fixtures; set `--start` to a desired Unix timestamp. `--interval` defaults to 900 seconds. Data is generated without wall-clock sleeping.

## Verification

Tests cover hierarchy cardinality, timestamps, seeded reproducibility, bounds, independent counters, invalid ranges, duplicate paths, and expansion limits. CI runs these tests and a small CLI smoke test.

A local smoke run of the included 400-sensor configuration generated 40,000 JSONL records in approximately 0.12 seconds, including process startup and file output, on Darwin arm64 with Python 3.14.3. This is a single local observation, not a distributed-system benchmark. Rerun the command on the target environment when reporting throughput.

The original prototype’s machine-specific path and external tree dependency have been removed. The simulator produces synthetic fixtures; it does not connect to physical devices, publish to a broker, or model correlated physical processes.
