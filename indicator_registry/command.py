from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from indicator_registry.statistics_office import Application, run, verify


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog='indicator_registry', description='人工智能治理指标口径版本与回算注册中心')
    commands = root.add_subparsers(dest="command", required=True)
    execute = commands.add_parser("run")
    execute.add_argument("--fixture", required=True)
    execute.add_argument("--database", required=True)
    execute.add_argument("--output", required=True)
    check = commands.add_parser("verify")
    check.add_argument("--database", required=True)
    check.add_argument("--output", required=True)
    check.add_argument("--report-id", default=None, help="verify a specific issued report")
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--database", required=True)
    versions = commands.add_parser("versions")
    versions.add_argument("--database", required=True)
    versions.add_argument("--definition-id", default=None)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "run":
        result = run(args.fixture, args.database, args.output)
    elif args.command == "verify":
        result = verify(args.database, args.output, report_id=args.report_id)
    elif args.command == "versions":
        result = Application(args.database).versions(args.definition_id)
    else:
        result = Application(args.database).inspect()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
