import datetime as dt
import unittest

from scripts.fetch_gfs import HOURS, LOCATIONS, REGIONS, candidate_cycles, make_record


UTC = dt.timezone.utc


class CandidateCyclesTests(unittest.TestCase):
    def test_uses_latest_published_six_hour_cycle(self):
        now = dt.datetime(2026, 11, 15, 14, 15, tzinfo=UTC)
        self.assertEqual(
            candidate_cycles(now, count=3),
            [
                dt.datetime(2026, 11, 15, 6, tzinfo=UTC),
                dt.datetime(2026, 11, 15, 0, tzinfo=UTC),
                dt.datetime(2026, 11, 14, 18, tzinfo=UTC),
            ],
        )

    def test_rolls_back_across_midnight(self):
        now = dt.datetime(2026, 11, 15, 8, 30, tzinfo=UTC)
        self.assertEqual(
            candidate_cycles(now, count=3),
            [
                dt.datetime(2026, 11, 15, 0, tzinfo=UTC),
                dt.datetime(2026, 11, 14, 18, tzinfo=UTC),
                dt.datetime(2026, 11, 14, 12, tzinfo=UTC),
            ],
        )

    def test_rejects_naive_datetime(self):
        with self.assertRaises(ValueError):
            candidate_cycles(dt.datetime(2026, 11, 15, 12))


class MakeRecordTests(unittest.TestCase):
    def test_calculates_meteorological_wind_direction(self):
        cycle = dt.datetime(2026, 11, 15, 0, tzinfo=UTC)
        fields = {
            "kirishima": {
                1000: {"u": 0.0, "v": -10.0, "gh": 120.0},
                975: {"u": -10.0, "v": 0.0, "gh": 340.0},
            }
        }
        rows = make_record(fields, cycle, 3)["locations"]["kirishima"]
        self.assertEqual(rows[0]["wind_direction_deg_from"], 0)
        self.assertEqual(rows[0]["wind_speed_ms"], 10.0)
        self.assertEqual(rows[1]["wind_direction_deg_from"], 90)

    def test_omits_incomplete_pressure_level(self):
        cycle = dt.datetime(2026, 11, 15, 0, tzinfo=UTC)
        fields = {"kirishima": {1000: {"u": 1.0, "v": 2.0}}}
        rows = make_record(fields, cycle, 3)["locations"]["kirishima"]
        self.assertEqual(rows, [])

    def test_includes_bounded_relative_humidity(self):
        cycle = dt.datetime(2026, 11, 15, 0, tzinfo=UTC)
        fields = {"kirishima": {1000: {"u": 1.0, "v": 2.0, "gh": 120.0, "r": 104.0}}}
        row = make_record(fields, cycle, 3)["locations"]["kirishima"][0]
        self.assertEqual(row["relative_humidity_percent"], 100)

    def test_includes_bounded_cloud_cover(self):
        cycle = dt.datetime(2026, 11, 15, 0, tzinfo=UTC)
        fields = {"kirishima": {1000: {"u": 1.0, "v": 2.0, "gh": 120.0, "tcc": 106.0}}}
        row = make_record(fields, cycle, 3)["locations"]["kirishima"][0]
        self.assertEqual(row["cloud_cover_percent"], 100)


class LocationConfigurationTests(unittest.TestCase):
    def test_forecasts_use_three_hour_intervals_through_72_hours(self):
        self.assertEqual(HOURS, list(range(3, 73, 3)))

    def test_every_location_is_assigned_to_one_fetch_region(self):
        assigned = [key for region in REGIONS.values() for key in region["locations"]]
        self.assertCountEqual(assigned, LOCATIONS)
        self.assertEqual(len(assigned), len(set(assigned)))

    def test_narashino_reference_point(self):
        point = LOCATIONS["narashino"]
        self.assertAlmostEqual(point["lat"], 35.70722400)
        self.assertAlmostEqual(point["lon"], 140.07658381)
        self.assertEqual(point["ground_elevation_m_msl_approx"], 29)

    def test_higashifuji_reference_point(self):
        point = LOCATIONS["higashifuji"]
        self.assertAlmostEqual(point["lat"], 35.26385539)
        self.assertAlmostEqual(point["lon"], 138.88753204)
        self.assertEqual(point["ground_elevation_m_msl_approx"], 464)


if __name__ == "__main__":
    unittest.main()
