from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "pack/overlays/v1_1_integration/config/mtsconfig.json"
POLICY = ROOT / "pack/overlays/v1_1_integration/drewcraft-integration/mts-fuel-policy.json"


def test_every_mts_fuel_category_accepts_only_lava_at_half_potency():
    config = json.loads(CONFIG.read_text())["fuel"]["fuels"]
    policy = json.loads(POLICY.read_text())
    expected = {"gasoline", "avgas", "diesel", "furnace", "brewing_stand"}

    assert set(config) == expected
    assert set(policy["fuel_categories"]) == expected
    assert all(fluids == {"lava": 0.5} for fluids in config.values())
    assert all(potency == 0.5 for potency in policy["fuel_categories"].values())
