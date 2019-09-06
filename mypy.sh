#! /bin/bash
# Type check.


mypy --strict --ignore-missing-imports "$1"
