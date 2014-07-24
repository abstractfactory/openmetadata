"""Open Metadata Command-line Interface

The command-line interface for Open Metadata. It operates on the
current working directory per default, but can be overridden via
the `root` flag. See example below.

Example:
    $ cd /home/marcus
    $ om write message "Hello World"
    $ om read message
    Hello World
    $ om write message "Hello World" --root="/home/marcus"
    $ om read message --root="/home/marcus"
    Hello World

    Relative path
    -------------

    The cli will use your current working directory if no root is
    specified. You can specify either an absolute or relative path:

    # This will join your cwd with "Building"
    $ om write Asset.class --root=Building

    # This will instead refer to an absolute path
    $ om write Asset.class --root=c:\Building


"""

import os
import sys
import openmetadata
import openmetadata.upgrade

from openmetadata.vendor import click


@click.group()
@click.option("--verbose", default=False)
@click.pass_context
def main(ctx, verbose):
    if not ctx.obj:
        ctx.obj = dict()

    ctx.obj['verbose'] = verbose
    verbose = verbose


@click.command()
@click.argument("path")
@click.option("--value", default=None)
@click.option("--root", default=None)
@click.pass_context
def write(ctx, path, value, root):
    """Write metadata.

    \b
    Usage:
        $ openmetadata write my_variable --value="Hello World"
        $ openmetadata write another_var --value=5

    """

    root = os.path.abspath(root) or os.getcwd()

    openmetadata.write(path=root,
                       metapath=path,
                       value=value)

    if ctx.obj.get('verbose'):
        sys.stdout.write("Success")


@click.command()
@click.argument("path")
@click.option("--root", default=None)
@click.pass_context
def read(ctx, path, root):
    """Read metadata.

    \b
    Usage:
        $ openmetadata read my_variable
        Hello World
        $ openmetadata read another_var
        5

    """

    root = os.path.abspath(root) or os.getcwd()

    sys.stdout.write(openmetadata.read(path=root,
                                       metapath=path))


@click.command()
@click.argument("mode", default="walk")
@click.option("--root", default=None)
@click.pass_context
def upgrade(ctx, mode, root):
    """Upgrade datastore to latest version.

    When an upgrade takes place, metadata is re-formatted to
    conform with the latest versions of Open Metadata. History
    for each completed formatting is stored at the root of
    the upgrade and may be invokated via a call to "restore".

    See below for an example.

    \b
    Usage:
        $ # Upgrade an old hierarchy to the latest version.
        $ openmetadata upgrade walk --root=subfolder
        $ # Roll back changes, leavning the datastore as
        $ # it was prior to running the upgrade.
        $ openmetadata upgrade restore

    """

    root = os.path.abspath(root) or os.getcwd()

    if mode == "walk":
        openmetadata.upgrade.walk(root)

    elif mode == "cwd":
        openmetadata.upgrade.cwd(root)

    elif mode == "restore":
        openmetadata.upgrade.restore(root)

    else:
        print "Mode not recognised"


@click.command()
@click.argument('echo', default="Hello world")
@click.option('--value', default=None)
@click.pass_context
def echo(ctx, echo, value):
    print echo, value


main.add_command(write)
main.add_command(read)
main.add_command(upgrade)
main.add_command(echo)
