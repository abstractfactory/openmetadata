"""Open Metadata package interface

This makes the Open Metadata package into an executable, via cli.py

"""

import logging
import openmetadata
import openmetadata.cli

if __name__ == '__main__':
    log = openmetadata.setup_log()
    log.setLevel(logging.WARNING)
    args = openmetadata.cli.parser.parse_args()

    openmetadata.cli.main(metapath=args.metapath,
                          value=args.value,
                          root=args.root)
