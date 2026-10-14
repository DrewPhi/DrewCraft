"""Conservative Linear/Chunky memory limits; leave heap and world data alone."""
import os
from pathlib import Path
import re
import tempfile
import tomllib


def atomic_text(path, text):
    stat = path.stat()
    fd, pending = tempfile.mkstemp(prefix=path.name+'.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(text)
        os.chmod(pending, stat.st_mode & 0o777)
        if os.geteuid() == 0:
            os.chown(pending, stat.st_uid, stat.st_gid)
        os.replace(pending, path)
    finally:
        if os.path.exists(pending):
            os.unlink(pending)


def apply(release):
    config = release/'config/linear-server.toml'
    original = config.read_text()
    tomllib.loads(original)
    updated, count = re.subn(r'(?m)^([ \t]*regionCacheSize[ \t]*=[ \t]*)\d+', r'\g<1>8', original)
    if count != 1 or tomllib.loads(updated).get('regionCacheSize') != 8:
        raise ValueError('Expected one root Linear regionCacheSize setting')
    args_path = release/'user_jvm_args.txt'
    args = args_path.read_text()
    revised, count = re.subn(r'(?<!\S)-Dchunky\.maxWorkingCount=\S+', '-Dchunky.maxWorkingCount=2', args)
    if count>1:
        raise ValueError('Ambiguous Chunky concurrency arguments')
    if not count:
        revised = args.rstrip()+'\n-Dchunky.maxWorkingCount=2\n'
    if original != updated:
        atomic_text(config, updated)
    if args != revised:
        atomic_text(args_path, revised)
    return {'regionCacheSize':8, 'chunkyMaxWorkingCount':2}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release', type=Path)
    print(apply(parser.parse_args().release))
