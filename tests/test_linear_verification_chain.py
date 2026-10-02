import sys
from pathlib import Path
from unittest.mock import patch
import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / 'infra'))
import linear_verification_chain as chain


def test_existing_selection_requires_and_uses_explicit_chunky_confirmation():
    with patch.object(chain, 'checked', side_effect=[
            '[Chunky] A task was already started for this world. Type /chunky confirm.',
            '[Chunky] Task started for minecraft:overworld.'] ) as command:
        assert 'Task started' in chain.start_chunky()
    assert [call.args for call in command.call_args_list] == [('chunky', 'start'), ('chunky', 'confirm')]


def test_chunky_does_not_treat_old_task_warning_as_success():
    with patch.object(chain, 'checked', return_value='A task was already started for this world.'):
        with pytest.raises(RuntimeError, match='did not acknowledge'):
            chain.start_chunky()


def test_chunky_requires_start_acknowledgement():
    with patch.object(chain, 'checked', return_value='No task running'):
        with pytest.raises(RuntimeError, match='did not acknowledge'):
            chain.start_chunky()
