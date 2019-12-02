#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import sys

from sys import exit

from wikidumpfilter.filter import run_filter
from wikidumpfilter.link import make_links


def main():
    parser = argparse.ArgumentParser(description='Preprocess MediaWiki dumps')
    subparsers = parser.add_subparsers(description='Available commands')
    parser.add_argument("-v", "--verbosity", action="count", default=0, dest='verbosity_level')
    parser_filter = subparsers.add_parser('filter', help='Extract wikipages that contain the math tag.',
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_filter.add_argument('-f', '--filename',
                               help="The bz2-file(s) to be split and filtered. You may use one/multiple file(s) or "
                                    "e.g. \"*.bz2\" as input.",
                               default=['enwiki-latest-pages-articles.xml.bz2'], dest='filenames', nargs='*')
    parser_filter.add_argument('-s', '--splitsize', help='The number of pages contained in each split.',
                               default=1000000, type=int, dest='size')
    parser_filter.add_argument('-d', '--outputdir', help='The directory name where the files go.', default='wout',
                               type=str, dest='dir')
    parser_filter.add_argument('-t', '--tagname', help='Tags to search for, e.g. use    -t TAG1 TAG2 TAG3',
                               default=['math', 'ce', 'chem', 'math chem'], type=str, dest='tags', nargs='*')
    parser_filter.add_argument('-k', '--keyword',
                               help='Keywords to search for, e.g. use    -k KEYWORD1 KEYWORD2 KEYWORD3   You might '
                                    'want '
                                    'to disable tags = specify empty tags (""), if you don`t want pages containing a '
                                    'tag OR a keyword!', default=[], type=str, dest='keywords', nargs='*')
    parser_filter.add_argument('-K', '--keyword_file',
                               help='Another way to specify keywords. Use a keyword file containing one keyword ('
                                    'e.g. "<title>formulae</title>") in each line.',
                               default='', type=str, dest='keyword_file')
    parser_filter.add_argument('-Q', '--QID_file',
                               help='QID-file, containing one QID (e.g. "Q1234") in each line. They will be '
                                    'translated to '
                                    'the titles in their respective languages and "<title>SOME_TITLE</title>" will '
                                    'be used '
                                    'as keywords. Specify languages with "-l". The languages will be taken from the '
                                    'beginning of the filenames, which thus must start with "enwiki"/"dewiki"/... for '
                                    'english/german/... !', default='', type=str, dest='QID_file')
    parser_filter.add_argument('-T', '--template', help='Include all templates.', action="store_true",
                               dest='template')  # default=False
    parser_filter.set_defaults(func=run_filter)

    parser_link = subparsers.add_parser('link',
                                        help='''Links all wiki-Dumps, except the ones already stored in the 
                                        given directory (does not include subdirectories). You may want to manually 
                                        delete/move them if you want to reprocess them too.''',
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_link.add_argument('-i', '--input_dir', help='The input directory name, where existing dumps are located.',
                             default='/public/dumps/public/', type=str)
    parser_link.add_argument('-o', '--output_dir',
                             help='The output directory name, where symbolic links will be created.',
                             default='/data/project/wdump/links/latest', type=str)
    parser_link.add_argument('-m', '--multistream', action="store_false")
    parser_link.set_defaults(func=make_links)

    parser_down = subparsers.add_parser('down',
                                        help=''''Downloads all wiki-Dumps, except the ones already stored in the 
                                        given directory(does not include subdirectories). You may want to manually 
                                        delete/move them if you want the program to download them too.''',
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_down.add_argument('-d', '--io_dir',
                             help='The input & output directory name, where (possibly) existing dumps are and '
                                  'downloaded '
                                  'ones should be stored. Defaults to current directory.',
                             default='./', type=str, dest='io_dir')
    parser_down.add_argument('-m', '--multistream', default=False)
    parser_down.set_defaults(func=download.down)

    args = parser.parse_args()
    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()
        exit(0)
