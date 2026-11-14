import unittest
from simulator import parse_config, records


class SimulatorTests(unittest.TestCase):
    def test_hierarchy_expansion_and_timestamps(self):
        sensors = parse_config('Building(2)/Floor(3)/Temperature Gauge#10,11')
        rows = list(records(sensors, steps=3, interval=30, start=100))
        self.assertEqual(len(sensors), 6)
        self.assertEqual(len(rows), 18)
        self.assertEqual([r['value'] for r in rows if r['path'] == '/Building1/Floor1/Temperature'], [10, 11, 10])
        self.assertEqual(sorted({r['timestamp'] for r in rows}), [100, 130, 160])

    def test_random_seed_and_bounds(self):
        sensors = parse_config('Device/Reading Random#4,8')
        first = list(records(sensors, steps=50, seed=7))
        self.assertEqual(first, list(records(sensors, steps=50, seed=7)))
        self.assertTrue(all(4 <= row['value'] <= 8 for row in first))
        self.assertNotEqual(first, list(records(sensors, steps=50, seed=8)))

    def test_counter_wraps_independently(self):
        sensors = parse_config('Device(2)/Count Counter#2,6,3')
        values = [r['value'] for r in records(sensors, steps=3)]
        self.assertEqual(values, [2, 2, 5, 5, 2, 2])

    def test_invalid_configurations(self):
        for text in ['', 'D Random#8,4', 'D Counter#1,2,0', 'D(0)/P Gauge#1,2', 'D Unknown#1,2', 'D Random#1,2\nD Random#1,2']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_config(text)
        with self.assertRaises(ValueError):
            parse_config('D(100001)/P Gauge#1,2')


if __name__ == '__main__':
    unittest.main()
