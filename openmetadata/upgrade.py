"""Automatic upgrade of hierarchy for migration to newer versions

This module is meant as an an alternative to manual migration and is
designed to be idempotent and safe. The upgrade is recorded and may be
restored at a later time via :func:restore()

Upgrading is non-atomic; meaning that data is written regardless of
future failures. This is so that even though the operation may fail,
history is still written so that you may still restore the original
hierarchy.

Attributes:
    LOG: Logger
    CONTAINER: Path in which metadata is stored
    ATTEMPTS: Number of times to perform a disk-write

"""

# Standard library
import os
import time
import errno
import logging

# Local library
import openmetadata.path

LOG = logging.getLogger('openmetadata.upgrade')
CONTAINER = openmetadata.path.Path.CONTAINER
ATTEMPTS = 10
HISTORY_FILE = '_history'


# ---------------------------------------------------------------------
#
# Exceptions
#
# ---------------------------------------------------------------------


class UpgradeError(Exception):
    pass


class HistoryError(Exception):
    pass


# ---------------------------------------------------------------------
#
# Body
#
# ---------------------------------------------------------------------


def walk(root=None):
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

    try:
        with open(history_path, 'a') as f:
            for base, dirs, _ in os.walk(root, topdown=True):
                if base.endswith(CONTAINER):
                    cwd_history = cwd(root=base, file_handle=f)
                    if cwd_history:
                        history.append(cwd_history)

                    # Do not walk into cwd
                    dirs[:] = []

    except IOError as e:
        if e.errno == errno.ENOENT:
            raise UpgradeError("Root doesn't exist: %s" % root)

    if history:
        LOG.info("Successfully upgraded {}, to restore run upgrade.restore")
    else:
        _remove(history_path)

    return history


def cwd(root=None, file_handle=None):
    """Upgrade metadata just within the current working directory

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


# ---------------------------------------------------------------------
#
# Helpers
#
# ---------------------------------------------------------------------


def _rename(src, dest):
    """Rename with attempts

    Upon failures on writes, attempt again after a fixed amount
    of times. If other errors occurs, raise an exception.

    Raises:
        UpgradeError: upon any errors

    """

    for attempt in xrange(ATTEMPTS):
        try:
            os.rename(src, dest)
        except EnvironmentError as e:
            print "# EXCEPTION: %s" % errno.errorcode[e.errno]

            if e.errno == errno.ENOENT:
                raise UpgradeError("Source did not exist: %s" % src)

            elif e.errno == errno.EACCES:
                raise UpgradeError("Source not writable: %s" % src)

            # In all other cases, sleep and try again
            LOG.warning("Failed attempt {}".format(attempt))
            time.sleep(0.1)

        else:
            return

    raise UpgradeError("Could not rename {} -> {}".format(src, e))


def _write(file_handle, line):
    """Write to disk with attempts.

    Arguments:
        file_handle (file): Handle to write to
        line (string): Data to write, in the form of "old -> new"

    """

    for attempt in xrange(ATTEMPTS):
        try:
            file_handle.write(line)
        except EnvironmentError as e:

            if e.errno == errno.ENOENT:
                raise UpgradeError(
                    "Source did not exist: %s" % file_handle.name)

            if e.errno == errno.EACCES:
                raise UpgradeError(
                    "Source not writable: %s" % file_handle.name)

            # In all other cases, sleep and try again
            LOG.warning("Failed attempt {}".format(attempt))
            time.sleep(0.1)
        else:
            return

    raise UpgradeError("Failed to write to {}: {}".format(file_handle.name, e))


def _remove(src):
    for attempt in xrange(ATTEMPTS):
        try:
            os.remove(src)
        except EnvironmentError as e:

            if e.errno == errno.ENOENT:
                raise UpgradeError("Source did not exist: %s" % src)

            if e.errno == errno.EACCES:
                raise UpgradeError("Source not writable: %s" % src)

            # In all other cases, sleep and try again
            LOG.warning("Failed attempt {}".format(attempt))
            time.sleep(0.1)

        else:
            return

    raise UpgradeError("Could not rename {} -> {}".format(src, e))
