"""CLI/import compatibility entry point for the shared launcher/server migrator."""
from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location('drewcraft_dh_config_upgrade', Path(__file__).resolve().parents[1] / 'launcher/dh_config_upgrade.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
migrate = module.migrate

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path)
    args = parser.parse_args()
    print('migrated' if migrate(args.config) else 'already schema 5')
