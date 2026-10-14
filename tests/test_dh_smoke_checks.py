import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('dh_smoke_checks', Path(__file__).parents[1] / 'tools/dh_smoke_checks.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


@pytest.mark.parametrize('blocks,chunks', [(1, 1), (16, 1), (17, 2), (32, 2), (512, 32)])
def test_block_radius_converted_to_native_dh_chunks(blocks, chunks):
    assert checks.dh_radius_chunks(blocks) == chunks


@pytest.mark.parametrize('reply,passes', [('#saved_block has 1 [dh_acceptance]', True),
                                        ('#saved_block has 0 [dh_acceptance]', False),
                                        ('#saved_block has 10 [dh_acceptance]', False),
                                        ('', False), ('Unknown scoreboard objective', False)])
def test_saved_block_uses_numeric_predicate_not_chat(reply, passes):
    calls = []
    def command(*args):
        calls.append(args)
        return reply if args[0:3] == ('scoreboard', 'players', 'get') else ''
    if passes:
        checks.verify_saved_block(command)
    else:
        with pytest.raises(AssertionError):
            checks.verify_saved_block(command)
    assert calls[0] == ('scoreboard', 'players', 'set', '#saved_block', 'dh_acceptance', '0')
    assert calls[1] == ('execute', 'store', 'success', 'score', '#saved_block', 'dh_acceptance',
                        'run', 'execute', 'if', 'block', '0', '65', '0', 'minecraft:diamond_block')
