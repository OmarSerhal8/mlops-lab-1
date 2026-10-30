from pathlib import Path
from types import SimpleNamespace

import pytest

from src.food11.promote import promote


class FakeClient:
    def __init__(self, candidate_accuracy):
        self.versions = {
            "8": SimpleNamespace(version="8", run_id="candidate"),
            "7": SimpleNamespace(version="7", run_id="champion"),
        }
        self.runs = {
            "candidate": SimpleNamespace(data=SimpleNamespace(metrics={"test_accuracy": candidate_accuracy})),
            "champion": SimpleNamespace(data=SimpleNamespace(metrics={"test_accuracy": 0.8})),
        }
        self.aliases = []
        self.tags = {}

    def get_model_version(self, _name, version):
        return self.versions[version]

    def get_model_version_by_alias(self, _name, alias):
        assert alias == "champion"
        return self.versions["7"]

    def get_run(self, run_id):
        return self.runs[run_id]

    def set_registered_model_alias(self, name, alias, version):
        self.aliases.append((name, alias, version))

    def set_model_version_tag(self, _name, _version, key, value):
        self.tags[key] = value


@pytest.mark.parametrize(
    ("accuracy", "expected"),
    [(0.90, "champion"), (0.82, "challenger")],
)
def test_promotion_gate(accuracy, expected):
    client = FakeClient(accuracy)
    assert promote(client, "food11", "8", 100, Path("data")) == expected
    assert client.aliases == [("food11", expected, "8")]
    assert client.tags["promotion_decision"] == expected
    assert client.tags["candidate_accuracy"] == str(accuracy)
    assert client.tags["champion_accuracy"] == "0.8"
