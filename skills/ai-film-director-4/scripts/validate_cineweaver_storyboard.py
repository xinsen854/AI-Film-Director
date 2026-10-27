#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from render_storyboard import validate_storyboard_payload, sequence_quality_warnings


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate CineWeaver SH/GU/PH structured storyboard payload')
    parser.add_argument('--input', required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding='utf-8'))
    errors = validate_storyboard_payload(data)
    if errors:
        print('FAIL')
        for error in errors:
            print('-', error)
        return 1
    warnings = sequence_quality_warnings(data)
    if warnings:
        print('WARN')
        for warning in warnings:
            print('-', warning)
    else:
        print('PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
