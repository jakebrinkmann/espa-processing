#! /usr/bin/env python
'ESPA Processing Command Line Interface'

from argparse import ArgumentParser
import logging

import cfg
import processor
from utilities import configure_base_logger
from schema import ProcessingRequestSchema

from . import __version__


def build_command_line_parser():
    """Builds the command line parser

    Returns:
        <parser>: Command line parser
    """

    parser = ArgumentParser(description=__doc__)

    parser.add_argument('--version',
                        action='version',
                        version=__version__)

    # ------------------------------------------------------------------------

    parser.add_argument('--input-product-id',
                        action='store',
                        dest='input_name',
                        required=True,
                        metavar='TEXT',
                        help='Input Product ID')

    parser.add_argument('--input-url',
                        action='store',
                        dest='input_urls',
                        required=True,
                        metavar='TEXT',
                        nargs='+',
                        help=('Complete URL path to the input product.'
                              '  Supported ("file://...", "http://...")'))

    parser.add_argument('--products',
                        action='store',
                        dest='products',
                        nargs="+",
                        help='Include Science Products')

    # ------------------------------------------------------------------------
    specific = parser.add_argument_group('metadata')

    specific.add_argument('--order-id',
                          action='store',
                          dest='order_id',
                          required=True,
                          metavar='TEXT',
                          help='Order ID')

    specific.add_argument('--product-type',
                          action='store',
                          dest='product_type',
                          required=True,
                          choices=['landsat', 'modis', 'plot'],
                          help='Type of product we are producing')

    specific.add_argument('--espa-api',
                          action='store',
                          dest='espa_api',
                          required=False, # TODO: REMOVE THIS
                          metavar='TEXT',
                          help='URL for the ESPA API')

    specific.add_argument('--work-dir',
                          action='store',
                          dest='work_dir',
                          required=False, # TODO: REMOVE THIS
                          metavar='TEXT',
                          help='Base processing directory')

    specific.add_argument('--dist-method',
                          action='store',
                          dest='dist_method',
                          required=False, # TODO: REMOVE THIS
                          choices=['local', 'remote'],
                          metavar='TEXT',
                          help='Distribution method')

    specific.add_argument('--dist-dir',
                          action='store',
                          dest='dist_dir',
                          required=False, # TODO: REMOVE THIS
                          metavar='TEXT',
                          help='Distribution directory')

    specific.add_argument('--bridge-mode',
                          action='store_true',
                          dest='bridge_mode',
                          help='Specify bridge processing mode')

    # ------------------------------------------------------------------------
    custom = parser.add_argument_group('customization')

    custom.add_argument('--resample-method',
                        action='store',
                        dest='resample_method',
                        choices=['near', 'bilinear', 'cubic',
                                 'cubicspline', 'lanczos'],
                        help='Resampling method to use')

    custom.add_argument('--pixel-size',
                        action='store',
                        dest='pixel_size',
                        metavar='FLOAT',
                        type=float,
                        help='Pixel size for the output product')

    custom.add_argument('--pixel-size-units',
                        action='store',
                        dest='pixel_size_units',
                        choices=['meters', 'dd'],
                        help='Units for the pixel size')

    custom.add_argument('--output-format',
                        action='store',
                        dest='output_format',
                        required=False,
                        choices=['envi', 'gtiff', 'hdf-eos2', 'netcdf'],
                        help='Output format for the product')

    # ------------------------------------------------------------------------
    extents = parser.add_argument_group('extents')

    extents.add_argument('--extent-units',
                         action='store',
                         dest='extent_units',
                         choices=['meters', 'dd'],
                         help='Units for the extent')

    extents.add_argument('--extent-minx',
                         action='store',
                         dest='minx',
                         metavar='FLOAT',
                         type=float,
                         help='Minimum X direction extent value')

    extents.add_argument('--extent-maxx',
                         action='store',
                         dest='maxx',
                         metavar='FLOAT',
                         type=float,
                         help='Maximum X direction extent value')

    extents.add_argument('--extent-miny',
                         action='store',
                         dest='miny',
                         metavar='FLOAT',
                         type=float,
                         help='Minimum Y direction extent value')

    extents.add_argument('--extent-maxy',
                         action='store',
                         dest='maxy',
                         metavar='FLOAT',
                         type=float,
                         help='Maximum Y direction extent value')

    # ------------------------------------------------------------------------
    projection = parser.add_argument_group('projection')

    projection.add_argument('--target-projection',
                            action='store',
                            dest='target_projection',
                            choices=['sinu', 'aea', 'utm', 'ps', 'lonlat'],
                            help='Reproject to this projection')

    projection.add_argument('--false-easting',
                            action='store',
                            dest='false_easting',
                            metavar='FLOAT',
                            type=float,
                            help='False Easting reprojection value')

    projection.add_argument('--false-northing',
                            action='store',
                            dest='false_northing',
                            metavar='FLOAT',
                            type=float,
                            help='False Northing reprojection value')

    projection.add_argument('--datum',
                            action='store',
                            dest='datum',
                            choices=['wgs84', 'nad27', 'nad83'],
                            help='Datum to use during reprojection')

    projection.add_argument('--utm-north-south',
                            action='store',
                            dest='utm_north_south',
                            choices=['north', 'south'],
                            help='UTM North or South')

    projection.add_argument('--utm-zone',
                            action='store',
                            dest='utm_zone',
                            metavar='INT',
                            type=int,
                            help='UTM Zone reprojection value')

    projection.add_argument('--central-meridian',
                            action='store',
                            dest='central_meridian',
                            metavar='FLOAT',
                            type=float,
                            help='Central Meridian reprojection value')

    projection.add_argument('--latitude-true-scale',
                            action='store',
                            dest='latitude_true_scale',
                            metavar='FLOAT',
                            type=float,
                            help='Latitude True Scale reprojection value')

    projection.add_argument('--longitude-pole',
                            action='store',
                            dest='longitude_pole',
                            metavar='FLOAT',
                            type=float,
                            help='Longitude Pole reprojection value')

    projection.add_argument('--origin-latitude',
                            action='store',
                            dest='origin_latitude',
                            metavar='FLOAT',
                            type=float,
                            help='Origin Latitude reprojection value')

    projection.add_argument('--std-parallel-1',
                            action='store',
                            dest='std_parallel_1',
                            metavar='FLOAT',
                            type=float,
                            help='Standard Parallel 1 reprojection value')

    projection.add_argument('--std-parallel-2',
                            action='store',
                            dest='std_parallel_2',
                            metavar='FLOAT',
                            type=float,
                            help='Standard Parallel 2 reprojection value')

    # ------------------------------------------------------------------------
    developer = parser.add_argument_group('developer')

    developer.add_argument('--dev-mode',
                           action='store_true',
                           dest='dev_mode',
                           help='Specify developer mode')

    developer.add_argument('--dev-intermediate',
                           action='store_true',
                           dest='dev_intermediate',
                           help='Specify keeping intermediate data files')

    developer.add_argument('--debug',
                           action='store_true',
                           dest='debug',
                           help='Specify debug logging')

    return parser


def reconstruct_group_schema(parser, args,
                             ignore=('optional arguments', 'positional arguments')):
    """ Convert flat argparse set to nested schema

    Args:
        parser (argparse.parser): schema tree where strings become args
        args (dict): key/value pairs supplied in flat format
        ignore (tuple): list of group titles to ignore

    Returns:
        dict: nested schema populated from args
    """
    return {group.title: {a.dest: getattr(args, a.dest, None)
                          for a in group._group_actions}
            for group in parser._action_groups
                if group.title not in ignore}


def clear_all_none(args):
    """ Strip all None from a key/value structure, including keys which nested them

    Args:
        args (dict): key/value pairs which may contain None values

    Returns:
        dict: structure with all None removed and no empty values

    Example:
        >>> clear_all_none({'a': 1, 'b': {'c': None}})
        {'a': 1}
    """
    return dict((x, y) for x, y in [
                (k, (v if not isinstance(v, dict) else clear_all_none(v)))
                for k, v in args.items() if v is not None ] if y != {})


def stack_projection_args(cli_args):
    """ Converts the flat processing options into nested JSON

    Args:
        cli_args (dict): arguments parsed from the CLI

    Returns:
        dict: nested dictionary grouped by types/usage

    Example:
        >>> stack_projection_args({'target_projection': 'utm', 'zone': 10})
        {'utm': {'zone': 10}}
    """
    return {cli_args.pop('target_projection'): cli_args}


def parse_command_line():
    """Parses the command line

    Returns:
        dict: Command line arguments
    """
    parser = build_command_line_parser()
    args = clear_all_none(reconstruct_group_schema(parser, parser.parse_args()))
    logging.debug('CLI Arguments: {}'.format(args))
    return args


def main():
    """ Command line entrypoint to process an order (stage, run, distrbute)
    """
    cli_args = parse_command_line()
    configure_base_logger(level='debug' if cli_args.get('debug') else 'info')
    processor.process(cfg, cli_args)
