#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse

from sys import exit

from wikidumpfilter.main import process_user_input, split_xml


def main():
    parser = argparse.ArgumentParser(description='Extract wikipages that contain the math tag.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-f', '--filename',
                        help='The bz2-file(s) to be split and filtered. You may use one/multiple file(s) or e.g. '
                             '"*.bz2" as input.',
                        default=['enwiki-latest-pages-articles.xml.bz2'], dest='filenames', nargs='*')
    parser.add_argument('-s', '--splitsize', help='The number of pages contained in each split.',
                        default=1000000, type=int, dest='size')
    parser.add_argument('-d', '--outputdir', help='The directory name where the files go.',
                        default='wout', type=str, dest='dir')
    parser.add_argument('-t', '--tagname', help='Tags to search for, e.g. use    -t TAG1 TAG2 TAG3',
                        default=['math', 'ce', 'chem', 'math chem'], type=str, dest='tags', nargs='*')
    parser.add_argument('-k', '--keyword',
                        help='Keywords to search for, e.g. use    -k KEYWORD1 KEYWORD2 KEYWORD3   You might want to '
                             'disable tags = specify empty tags (""), if you don`t want pages containing a tag OR a '
                             'keyword!',
                        default=[], type=str, dest='keywords', nargs='*')
    parser.add_argument('-K', '--keyword_file',
                        help='Another way to specify keywords. Use a keyword file containing one keyword (e.g. '
                             '"<title>formulae</title>") in each line.',
                        default='', type=str, dest='keyword_file')
    parser.add_argument('-Q', '--QID_file',
                        help='QID-file, containing one QID (e.g. "Q1234") in each line. They will be translated to '
                             'the titles in their respective languages and "<title>SOME_TITLE</title>" will be used '
                             'as keywords. Specify languages with "-l". The languages will be taken from the '
                             'beginning of the filenames, which thus must start with "enwiki"/"dewiki"/... for '
                             'english/german/... !',
                        default='', type=str, dest='QID_file')
    parser.add_argument("-v", "--verbosity", action="count", default=0, dest='verbosity_level')
    parser.add_argument('-T', '--template', help='Include all templates.',
                        action="store_true", dest='template')  # default=False
    args = parser.parse_args()

    tags, keywords, languages, lang_with_titles, filenames = \
        process_user_input(args.keywords, args.keyword_file, args.QID_file, args.filenames, args.tags, args.dir,
                           args.verbosity_level)

    for filename in filenames:
        language = filename.split("wiki")[0]

        current_keywords = keywords[:]
        if args.QID_file != '':
            current_keywords += lang_with_titles[language]  # add titles as keywords

        split_xml(filename, args.size, args.dir, tags, args.template, current_keywords, args.verbosity_level)
