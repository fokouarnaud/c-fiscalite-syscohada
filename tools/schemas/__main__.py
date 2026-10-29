"""python -m tools.schemas <formation> : écrit les schémas de la formation."""
import argparse

from . import common, compta, fisca

FORMATIONS = {module.SLUG: module for module in (compta, fisca)}

parser = argparse.ArgumentParser(prog="python -m tools.schemas", description=__doc__)
parser.add_argument("formation", choices=sorted(FORMATIONS))
common.write_formation(FORMATIONS[parser.parse_args().formation])
