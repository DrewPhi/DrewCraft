"""Protocol checks for disposable DH acceptance worlds; no live-server access."""
import re


def dh_radius_chunks(radius_blocks):
    if not isinstance(radius_blocks, int) or radius_blocks <= 0:
        raise ValueError('Expected a positive block radius')
    return (radius_blocks + 15) // 16


def verify_saved_block(command):
    # /say is a broadcast, not a reliable RCON return value. Store the actual
    # predicate result and query it explicitly; a failed predicate stores zero.
    command('scoreboard', 'players', 'set', '#saved_block', 'dh_acceptance', '0')
    command('execute', 'store', 'success', 'score', '#saved_block', 'dh_acceptance',
            'run', 'execute', 'if', 'block', '0', '65', '0', 'minecraft:diamond_block')
    reply = command('scoreboard', 'players', 'get', '#saved_block', 'dh_acceptance')
    if not re.search(r'#saved_block has 1 \[dh_acceptance\]', reply):
        raise AssertionError(f'Saved-block predicate failed or could not be read: {reply!r}')
