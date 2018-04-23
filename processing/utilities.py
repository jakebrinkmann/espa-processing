
""" Host system utilities for espa-processing """

import os
import sys
import errno
import datetime
import shlex
try:
    import resource
except:
    resource = None

import logging
import subprocess
from collections import defaultdict


DATE_FMT = r'%Y-%m-%d %H:%M:%S'
LOG_LINE_FORMAT = (
    '%(asctime)s.%(msecs)03d %(process)d %(levelname)-8s '
    '%(filename)s:%(lineno)d:%(funcName)s -- %(message)s'
)


def configure_base_logger(stream='stdout', format=LOG_LINE_FORMAT,
                          datefmt=DATE_FMT, level='INFO'):
    """ Configures the base logger to an output stream

    Args:
        stream (str): The name of the output stream (stderr/stdout)
        format (str): The formatting to use withiin the log lines
        datefmt (str): The format for the date strings
        level (str): The base level of errors to log to the handler
    """
    logging.basicConfig(stream=getattr(sys, stream.lower()),
                        format=format,
                        datefmt=datefmt,
                        level=getattr(logging, level.upper()))


def peak_memory_usage(this=False):
    """ Get the peak memory usage of all children processes (Linux-specific KB->Byte implementation)

    Args:
        this (bool): Flag to instead get usage of this calling process (not including children)

    Returns:
        usage (float): Usage in bytes
    """
    who = resource.RUSAGE_CHILDREN
    if this is True:
        # NOTE: RUSAGE_BOTH also exists, but not available everywhere
        who = resource.RUSAGE_SELF
    info = resource.getrusage(who)
    usage = info.ru_maxrss * 1024
    return usage


def current_disk_usage(pathname):
    """ Get the total disk usage of a filesystem path

    Args:
        pathname (str): Relative/Absolute path to a filesystem resource

    Returns:
        usage: (int): Usage in bytes
    """
    dirs_dict = defaultdict(int)
    for root, dirs, files in os.walk(pathname, topdown=False):
        size = sum(os.path.getsize(os.path.join(root, name))
                   if os.path.exists(os.path.join(root, name)) else 0 for name in files)
        subdir_size = sum(dirs_dict[os.path.join(root, d)] for d in dirs)
        my_size = dirs_dict[root] = size + subdir_size
    return dirs_dict[pathname]


def snapshot_resources(log=True):
    """ Delivers (to logger) a current resource snapshot in JSON format

    Args:
        log (bool): flag to log resources to logging

    Returns:
        dict: resource usage
    """
    resources = {
        'current_disk_usage': current_disk_usage(os.getcwd()),
        'peak_memory_usage': peak_memory_usage()
    }
    if log:
        logging.warning('Resources: {}'.format(resources))
    return resources


def watch_stdout(cmd):
    """ Combine stdout/stderr, read output in real time, return execution results

    Args:
        cmd (list): command and arguments to execute

    Returns:
        dict: exit status code and text output stream from stdout
    """
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
    output = []
    for line in iter(process.stdout.readline, b''):
        logging.debug(line.strip())
        output.append(line.strip())
        if process.poll() is not None:
            break
    process.stdout.close()
    process.wait()
    return {
        'status': process.returncode,
        'output': '\n'.join(output)
    }


def execute_cmd(cmd):
    """ Execute a system command line call, raise error on non-zero exit codes

    Args:
        cmd (str): The command line to execute.

    Returns:
        dict: exit status code and text output stream from stdout
    """

    cparts = cmd
    if isinstance(cmd, str):
        cparts = shlex.split(cmd)
    results = watch_stdout(cmd)

    message = ''
    if results['status'] < 0:
        message = 'Application terminated by signal [{}]'.format(cmd)

    if results['status'] != 0:
        message = 'Application failed to execute [{}]'.format(cmd)

    if os.WEXITSTATUS(results['status']) != 0:
        message = ('Application [{}] returned error code [{}]'
                   .format(cmd, os.WEXITSTATUS(results['status'])))

    if len(message) > 0:
        if len(results['output']) > 0:
            # Add the output to the exception message
            message = ' Stdout/Stderr is: '.join([message, results['output']])
        raise Exception(message)

    return results


def create_directory(directory):
    """Create the specified directory with some error checking

    Args:
        directory (str): The full path to create.

    Raises:
        Exception()
    """

    # Create/Make sure the directory exists
    try:
        os.makedirs(directory, mode=0755)
    except OSError as ose:
        if ose.errno == errno.EEXIST and os.path.isdir(directory):
            # With how we operate, as long as it is a directory, we do not
            # care about the 'already exists' error.
            pass
        else:
            raise


def create_link(src_path, link_path):
    """Create the specified link with some error checking

    Args:
        src_path (str): The location where the link will point.
        link_path (str): The location where the link will reside.

    Raises:
        Exception()
    """

    # Create/Make sure the directory exists
    try:
        os.symlink(src_path, link_path)
    except OSError as ose:
        if (ose.errno == errno.EEXIST and os.path.islink(link_path) and
                src_path == os.path.realpath(link_path)):
            pass
        else:
            raise


def untar_cmd(src, dest):
    """ Create the tar commandline call

    Args:
        src (str): relative or full path to source tar file
        dest (str): full path to output directory

    Returns:
        str: the tar command ready for execution

    Examples:
        >>> untar_cmd('my.tar.gz', '/path/to/place')
        'tar --directory /path/to/place -xvf my.tar.gz'
    """
    return ' '.join(['tar', '--directory', dest, '-xvf', src])


def untar_data(source_file, destination_directory):
    '''
    Description:
        Using tar extract the file contents into a destination directory.

    Notes:
        Works with '*.tar.gz' and '*.tar' files.
    '''
    logging.info("Unpacking [%s] to [%s]",
                 source_file, destination_directory)

    # Unpack the data and raise any errors
    output = ''
    try:
        output = execute_cmd(untar_cmd(source_file, destination_directory))
    except Exception:
        logging.exception("Failed to unpack data")
        raise
