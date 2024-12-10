"""
    fryweb.__main__
    ~~~~~~~~~~~~~~~

    Main entry point for ``python -m fryweb``

    :copyright: Copyright 2023 by zenkj<juzejian@gmail.com>
    :license: MIT, see LICENSE for details.
"""

import sys
from fryweb.cmdline import main

try:
    sys.exit(main())
except KeyboardInterrupt:
    sys.exit(1)
