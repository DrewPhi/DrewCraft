from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
from verify_pregen_memory_recovery import radius


def test_native_dh_radius_is_not_confused_with_rate_eta_or_target():
    assert radius('Generated radius: 32.75 / 708 chunks (49 cps, 0.214%), ETA: 01:05:00')==32.75
    assert radius('Pregen is not running') is None
    assert radius('Starting pregen at -1536, -1536 with radius 708') is None
