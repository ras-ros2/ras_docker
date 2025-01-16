"""
Copyright (C) 2024 Harsh Davda

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

For inquiries or further information, you may contact:
Harsh Davda
Email: info@opensciencestack.org
"""

import argparse
import subprocess
import os,sys
from pathlib import Path
import vcstool,json,yaml
from functools import partial
from enum import Enum
from dataclasses import dataclass, field, InitVar


from ras_docker.arg_parser import get_parser,parse_args
def main():
    parser = get_parser()
    parse_args(parser)
    
if __name__ == "__main__":
    main()
