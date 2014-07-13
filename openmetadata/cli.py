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

Datatypes:
    As inpute from the command-line is all strings, certain types are
    automatically cast to their relevant types. Those are:

    - bool
    - None
    - int/float

Relative path:
    The cli will use your current working directory if no root is
    specified. You can specify either an absolute or relative path:

    $ # This will join your cwd with "Building"
    $ openmetadata Asset.class --root=Building

    $ # This will instead refer to an absolute path
    $ openmetadata Asset.class --root=c:\Building


"""

import os
import sys
import argparse
import openmetadata


def cli(metapath,
        value='',
        root=None,
        verbose=False):

    """Command-line interface interpterer

    Arguments:
        metapath (str): Full meta-path to metadata, e.g. "/address/street"
        value (str, optional): Pass a value to write as opposed to read
        root (str, optional): cli writes to the cwd by default, this is
            an override, as a relative path. E.g. root="subfolder"
        verbose (bool): Output more information

    """

    root = root

    if root:
        root = os.path.abspath(root)
    else:
        root = os.getcwd()

    value = value

    # Cast input

    try:
        value = float(value)

        if value == int(value):
            value = int(value)

    except:
        pass

    if value == 'None':
        value = None

    elif value == 'True':
        value = True

    elif value == 'False':
        value = False

    if value is not '':
        openmetadata.write(path=root,
                           metapath=metapath,
                           value=value)

        if verbose:
            sys.stdout.write("Success")

    else:
        print openmetadata.read(path=root,
                                metapath=metapath)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('metapath')
    parser.add_argument('--value', default='')
    parser.add_argument('--root', default=None)

    args = parser.parse_args()

    cli(metapath=args.metapath,
        value=args.value,
        root=args.root)
