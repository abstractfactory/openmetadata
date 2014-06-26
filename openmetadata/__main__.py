"""Open Metadata Command-line Interface

The command-line interface for Open Metadata. It operates on the
current working directory per default, but can be overridden via
the `root` flag. See example below.

Example:
    $ cd /home/marcus
    $ openmetadata message --value="Hello World"
    $ openmetadata message
    Hello World
    $ openmetadata message --value="Hello World" --root="/home/marcus"
    $ openmetadata message --root="/home/marcus"
    Hello World

"""

import os
import sys
import logging
import argparse
import openmetadata

log = openmetadata.setup_log()
log.setLevel(logging.WARNING)

parser = argparse.ArgumentParser()
parser.add_argument('metapath')
parser.add_argument('--value', default=None)
parser.add_argument('--root', default=os.getcwd())

args = parser.parse_args()

if args.value is not None:
    openmetadata.write(path=args.root,
                       metapath=args.metapath,
                       value=args.value)
    sys.stdout.write("Success")

else:
    print openmetadata.read(path=args.root,
                            metapath=args.metapath)
