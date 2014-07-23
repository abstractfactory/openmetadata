"""Automatic upgrade of hierarchy for migration to newer versions

This module is meant as an an alternative to manual migration and is
designed to be idempotent and safe. An history


Attributes:
    LOG: Logger
    CONTAINER: Path in which metadata is stored
    ATTEMPTS: Number of times to perform a disk-write

"""

import os
import time
import errno
import logging
import openmetadata.path
from openmetadata.vendor import click

LOG = logging.getLogger('openmetadata.upgrade')
CONTAINER = openmetadata.path.Path.CONTAINER
ATTEMPTS = 10
HISTORY_FILE = '_history'


class UpgradeError(Exception):
    pass


class HistoryError(Exception):
    pass


@click.command()
@click.option('--test', default=False)
def cli(test):
    print test


def hierarchy_cli(root=None):
    return hierarchy(root)


def container_cli(root=None):
    return container(root)


def restore_cli(root=None):
    return restore(root)


def hierarchy(root=None):
    """Upgrade all metadata within hierarchy starting at `root`

    Arguments:
        root (str): Absolute path to location from which a walk will
            commence through the subsequent hierarchy.

    Raises:
        HistoryError: when failing to write history
        UpgradeError: when failing to upgrade

    """

    root = root or os.getcwd()

    history = list()

    history_path = os.path.join(root, HISTORY_FILE)
    with open(history_path, 'a') as f:
        for base, dirs, _ in os.walk(root, topdown=True):
            if base.endswith(CONTAINER):
                container_history = container(root=base, file_handle=f)
                if container_history:
                    history.append(container_history)

                # Do not walk into container
                dirs[:] = []

    if history:
        LOG.info("Successfully upgraded {}, to restore run upgrade.restore")
    else:
        _remove(history_path)

    return history


def container(root=None, file_handle=None):
    """Upgrade metadata just within the container at `root`

    The rule is that directories without suffix are assumed
    to be of type dict.

    Arguments:
        root (str): Absolute path to location, the inner container
            will be upgraded.

    Raises:
        HistoryError: when failing to write history
        UpgradeError: when failing to upgrade

    """

    root = root or os.getcwd()

    if not root.endswith(CONTAINER):
        root = os.path.join(root, CONTAINER)

    history = list()

    if file_handle:
        # If a handle has been passed, we trust the caller to
        # close the file once done.
        close = False
    else:
        history_path = os.path.join(root, HISTORY_FILE)
        file_handle = open(history_path, 'a')
        close = True

    try:
        for base, dirs, _ in os.walk(root, topdown=True):
            # With topdown=True we perform in-place edits of
            # the hierarchy as we go. See the docs on os.walk
            # for more information.

            assert CONTAINER in base

            for dir in dirs:
                if not "." in dir:
                    new_dir = dir + ".dict"

                    previous_path = os.path.join(base, dir)
                    new_path = os.path.join(base, new_dir)
                    line = "%s -> %s\n" % (new_path, previous_path)
                    history.append(line)

                    _rename(previous_path, new_path)

                    # Alter walk and make history
                    dirs[dirs.index(dir)] = new_dir
                    _write(file_handle, line)

    finally:
        if close:
            file_handle.close()
            if not history:
                _remove(history_path)

    return history


def restore(root=None):
    """Undo an upgrade operation

    Arguments:
        cache (str): An absolute path to location or container
            to history.

    Raises:
        HistoryError: when failing to write history
        UpgradeError: when failing to upgrade
        ValueError: when no history is present

    """

    root = root or os.getcwd()

    history_path = os.path.join(root, HISTORY_FILE)

    try:
        print "# Opening %s" % history_path
        with open(history_path, 'r') as f:
            history = f.read()
    except IOError as e:
        if e.errno == errno.ENOENT:
            raise ValueError("No history cache found")

    # History is recorded depth-first:
    #
    # /group1
    # /group1/group2
    # /group1/group2/group3
    #
    # For a restore operation to work, we'll have to apply each
    # change in reverse so as to not invalidate the path for children:
    #
    # /group1.dict/group2.dict/group3.dict >> /group1.dict/group2.dict/group3
    # /group1.dict/group2.dict >> /group1.dict/group2
    # /group1.dict >> /group1

    history = history.split("\n")
    history.reverse()

    for line in history:
        if not line:
            continue

        current_path, previous_path = line.split(" -> ")
        _rename(current_path, previous_path)

    _remove(history_path)


def restorable(root=None):
    """Return whether or not absolute path `root` is restorable"""
    root = root or os.getcwd()
    history_path = os.path.join(root, HISTORY_FILE)
    return os.path.isfile(history_path)


def _rename(src, dest):
    for attempt in xrange(ATTEMPTS):
        try:
            os.rename(src, dest)
        except IOError as exc:
            LOG.warning("Failed attempt {}".format(attempt))
            time.sleep(0.1)
        else:
            return

    raise UpgradeError("Could not rename {} -> {}".format(src, exc))


def _write(file_handle, line):
    for attempt in xrange(ATTEMPTS):
        try:
            file_handle.write(line)
        except IOError as exc:
            LOG.warning("Failed attempt {}".format(attempt))
            time.sleep(0.1)
        else:
            return

    raise IOError("Failed to write to {}: {}".format(file_handle.name, exc))


def _remove(src):
    exc = None
    for attempt in xrange(ATTEMPTS):
        try:
            os.remove(src)
        except Exception as e:
            LOG.warning("Failed attempt {}".format(attempt))
            time.sleep(0.1)
            exc = e
        else:
            return

    raise IOError("Could not rename {} -> {}".format(src, exc))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--hierarchy', action='store_true', default=False)
    parser.add_argument('--container', action='store_true', default=False)
    parser.add_argument('--restore', action='store_true', default=False)

    args = parser.parse_args()
    if (args.hierarchy + args.container + args.restore) != 1:
        print "See help for instructions on how to use this utility"

    elif args.hierarchy:
        hierarchy()

    elif args.container:
        container()

    elif args.restore:
        restore()
