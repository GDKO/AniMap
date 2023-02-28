#!/usr/bin/env python3

"""
  Usage:
    animap [<module>] [<args>...] [-h] [-v]

  Modules:
    region         animate module for a specific region
    world          animate module for earth

  Options
    -h, --help      show this
    -v, --version   show version number

    See 'animap <command> --help' for more information on a specific command.

"""

import sys
from docopt import docopt

def main():
    args = docopt(__doc__,version='1.0.1', options_first=True)
    if args['<module>'] == 'region':
        import depot.region as region
        region.main()
    elif args['<module>'] == 'world':
        import depot.world as world
        world.main()
    else:
        sys.exit("%r is not an animap module. See 'animap -h'." % args['<module>'])
