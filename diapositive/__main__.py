import argparse
import logging
from pathlib import Path

from . import NAME, VERSION
from .models import Site


def main():
    parser = argparse.ArgumentParser(
        prog="diapo",
        description="simple photo gallery generator",
    )
    parser.add_argument(
        metavar="PHOTODIR", type=Path, dest="indir",
        help="input directory",
    )
    parser.add_argument(
        "-o", "--outdir", metavar="DIR", type=Path,
        default=Path("./_site"), help="output directory (default: ./_site)",
    )
    parser.add_argument(
        "-C", "--config", metavar="PATH", type=Path,
        help="configuration file (default: <PHOTODIR>/diapositive.toml)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="show more verbose output",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true",
        help="show very verbose output",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"{NAME} {VERSION}",
    )
    args = parser.parse_args()

    logging.basicConfig(format="%(levelname)s: %(message)s",
                        level=logging.DEBUG if args.debug else (
                            logging.INFO if args.verbose else logging.WARNING
                        ))
    logging.captureWarnings(True)
    logger = logging.getLogger(__name__)

    print(f"{NAME} {VERSION}")

    cfg = args.config or (args.indir / "diapositive.hcl")
    logger.info(f"using config file: {cfg}")
    logger.info(f"using input directory: {args.indir}")
    logger.info(f"using output directory: {args.outdir}")
    site = Site.from_config(cfg)
    site.read_albums(args.indir)
    site.write(args.outdir)
    logger.info("site built")
