""" Abstraction for interfacing with providers.yml """

import yaml


def read_yaml(filename='processing/providers.yaml'):
    """ Parse a YAML file from filesystem

    Args:
        filename (str): relative path to providers yaml

    Returns:
        dict: serialized data from file
    """
    return yaml.load(open(filename))


def make_cmd(entity):
    """ Convert YAML entry into commandline call

    Args:
        entity (dict): The serialzied represntation of command

    Returns:
        str: The formatted string

    Example:
        >>> make_cmd({"cmd": "echo", "args": "hello"})
        'echo hello'
    """
    return '{cmd} {args}'.format(**entity)


def find_product(product, providers):
    """ Extracts only the provider which produces a product

    Args:
        product (str): producer to search providers for
        providers (dict): parsed yaml providers descriptions

    Returns:
        dict: single key entry from providers

    Example:
        >>> find_product('thing', {'i1': {'products': ['thing']}})
        {'i1': {'products': ['thing']}}
    """
    return {name: description for name, description in providers.items()
            if product in description.get('products')}


def sequence(product, input_id):
    a = read_yaml()
    p = find_product(product, a)