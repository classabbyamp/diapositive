import argparse
import logging
import os
from pathlib import Path

from . import NAME
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
        "-u", "--baseurl", metavar="URL", type=str,
        default="", help="base URL for serving the site (overrides configuration)",
    )
    parser.add_argument(
        "-j", "--jobs", metavar="N", type=int,
        default=os.process_cpu_count(), help="number of jobs for parallel processing (default: number of available CPUs)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="show more verbose output",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true",
        help="show very verbose output",
    )
    args = parser.parse_args()

    logging.addLevelName(logging.DEBUG, "\033[0;35mD\033[0m")
    logging.addLevelName(logging.INFO, "\033[0;34mI\033[0m")
    logging.addLevelName(logging.WARNING, "\033[0;33mW\033[0m")
    logging.addLevelName(logging.ERROR, "\033[0;31mE\033[0m")
    logging.addLevelName(logging.CRITICAL, "\033[1;31m!\033[0m")
    logging.basicConfig(format="[%(levelname)s] %(message)s",
                        level=logging.DEBUG if args.debug else (
                            logging.INFO if args.verbose else logging.WARNING
                        ))
    logging.captureWarnings(True)
    logger = logging.getLogger(__name__)
    pillow_logger = logging.getLogger("PIL")
    pillow_logger.setLevel(logging.WARNING)

    print(NAME)

    cfg = args.config or (args.indir / "diapositive.hcl")
    logger.info(f"using {args.jobs} jobs")
    logger.info(f"using config file: {cfg}")
    logger.info(f"using input directory: {args.indir}")
    logger.info(f"using output directory: {args.outdir}")
    try:
        site = Site.from_config(cfg)
        if args.baseurl:
            logger.debug(f"overriding base_url from command-line: {args.baseurl}")
            site.base_url = args.baseurl
        if args.debug:
            logger.debug(site)
        site.read_albums(args.indir, args.jobs)
        site.write(args.outdir, args.jobs)
    except Exception as e:
        logger.critical(f"fatal {type(e).__name__}: {e}")
        exit(1)
    logger.info("site built")
