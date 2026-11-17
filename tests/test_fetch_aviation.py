import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest import mock


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "fetch_aviation.py"
SPEC = importlib.util.spec_from_file_location("fetch_aviation", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FetchAviationTests(unittest.TestCase):
    def test_station_groups_cover_all_locations(self):
        self.assertEqual(set(MODULE.STATIONS), {"kirishima", "tanegashima", "narashino"})
        self.assertEqual(MODULE.STATIONS["narashino"], ["RJAA", "RJTT"])
        self.assertTrue(all(len(stations) == 2 for stations in MODULE.STATIONS.values()))

    def test_fetch_rejects_non_list_response(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({"bad": True}).encode()
        with mock.patch.object(MODULE.urllib.request, "urlopen", return_value=response):
            with self.assertRaisesRegex(ValueError, "Unexpected"):
                MODULE.fetch("metar", {"format": "json"})

    def test_main_filters_sigmet_to_fukuoka_fir(self):
        replies = {
            "metar": [{"icaoId": "RJAA"}],
            "taf": [{"icaoId": "RJAA"}],
            "isigmet": [{"firId": "RJJJ", "hazard": "TURB"}, {"firId": "KZNY"}],
        }
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            MODULE, "fetch", side_effect=lambda endpoint, query: replies[endpoint]
        ), mock.patch.object(MODULE.Path, "cwd", return_value=pathlib.Path(directory)):
            old_cwd = pathlib.Path.cwd()
            try:
                import os
                os.chdir(directory)
                MODULE.main()
                payload = json.loads(pathlib.Path("data/aviation_weather.json").read_text())
            finally:
                os.chdir(old_cwd)
        self.assertEqual(payload["sigmets_fukuoka_fir"], [{"firId": "RJJJ", "hazard": "TURB"}])
        self.assertEqual(payload["status"], "ok")


if __name__ == "__main__":
    unittest.main()
