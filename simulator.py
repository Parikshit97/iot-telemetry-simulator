"""Generate deterministic telemetry from hierarchical sensor configuration."""
import argparse
import csv
import itertools
import json
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Sensor:
    path: str
    kind: str
    minimum: int
    maximum: int
    step: int


def parse_config(text, max_sensors=100000):
    sensors, seen = [], set()
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        try:
            hierarchy, expression = line.split()
            kind, arguments = expression.split('#')
            values = [int(value) for value in arguments.split(',')]
            if kind not in ['Random', 'Gauge', 'Counter'] or len(values) != (3 if kind == 'Counter' else 2):
                raise ValueError('use Random#min,max, Gauge#min,max, or Counter#min,max,step')
            minimum, maximum = values[:2]
            step = values[2] if kind == 'Counter' else 1
            if minimum > maximum or step <= 0:
                raise ValueError('minimum must not exceed maximum and step must be positive')
            levels = []
            count = 1
            for segment in hierarchy.split('/'):
                match = re.fullmatch(r'([A-Za-z_][A-Za-z0-9_-]*)(?:\(([0-9]+)\))?', segment)
                if not match:
                    raise ValueError('invalid hierarchy segment')
                name, instances = match.groups()
                instances = int(instances or 1)
                count *= instances
                if instances < 1 or count + len(sensors) > max_sensors:
                    raise ValueError(f'configuration exceeds the {max_sensors} sensor limit or has a zero instance count')
                levels.append([name] if instances == 1 else [f'{name}{i}' for i in range(1, instances + 1)])
            for parts in itertools.product(*levels):
                path = '/' + '/'.join(parts)
                if path in seen:
                    raise ValueError('duplicate sensor path')
                seen.add(path)
                sensors.append(Sensor(path, kind, minimum, maximum, step))
        except ValueError as error:
            raise ValueError(f'configuration line {number}: {error}') from error
    if not sensors:
        raise ValueError('configuration contains no sensors')
    return sensors


def records(sensors, steps=100, interval=900, start=0, seed=42):
    if steps < 1 or interval <= 0:
        raise ValueError('steps and interval must be positive')
    rng = random.Random(seed)
    states = {sensor.path: sensor.minimum for sensor in sensors}
    for index in range(steps):
        for sensor in sensors:
            value = rng.randint(sensor.minimum, sensor.maximum) if sensor.kind == 'Random' else states[sensor.path]
            yield {'path': sensor.path, 'timestamp': start + index * interval, 'value': value}
            next_value = value + sensor.step
            states[sensor.path] = sensor.minimum if next_value > sensor.maximum else next_value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).with_name('config.txt'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--format', choices=['jsonl', 'csv'], default='jsonl')
    parser.add_argument('--steps', type=int, default=100)
    parser.add_argument('--interval', type=int, default=900, help='seconds between simulated timestamps')
    parser.add_argument('--start', type=int, default=0, help='Unix timestamp of the first sample')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--max-sensors', type=int, default=100000)
    args = parser.parse_args()
    try:
        sensors = parse_config(args.config.read_text(), args.max_sensors)
        stream = records(sensors, args.steps, args.interval, args.start, args.seed)
        output = args.output.open('w', newline='') if args.output else sys.stdout
        try:
            if args.format == 'csv':
                writer = csv.DictWriter(output, fieldnames=['path', 'timestamp', 'value'])
                writer.writeheader()
                writer.writerows(stream)
            else:
                for record in stream:
                    output.write(json.dumps(record) + '\n')
        finally:
            if args.output:
                output.close()
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
