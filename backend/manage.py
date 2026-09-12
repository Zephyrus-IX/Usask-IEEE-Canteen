#!/usr/bin/env python
import os
import sys


def main() -> None:
    settings_module = (
        "canteen_project.test_settings"
        if len(sys.argv) > 1 and sys.argv[1] == "test"
        else "canteen_project.settings"
    )
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
