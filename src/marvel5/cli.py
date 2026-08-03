"""Thin CLI wrapper: parse -> solve -> write, same MarvelRun the viz app uses."""

import argparse

from .run import MarvelRun


def main() -> None:
    p = argparse.ArgumentParser(prog="marvel5")
    p.add_argument("input", help="MRT-format transitions file")
    p.add_argument("-o", "--output-dir", default=".", help="directory for <run>_levels.csv / <run>_transitions.csv")
    p.add_argument("--bootstrap-iterations", type=int, default=100)
    p.add_argument("--cutoff", type=float, default=10.0, help="offender-ratio consistency cutoff")
    args = p.parse_args()

    run = MarvelRun.from_file(args.input)
    run.solve(bootstrap_iterations=args.bootstrap_iterations, cutoff=args.cutoff)
    run.write_output(args.output_dir)
    print(f"solved {len(run._transitions)} transitions -> {len(run._levels)} levels; wrote {args.output_dir}")


if __name__ == "__main__":
    main()
