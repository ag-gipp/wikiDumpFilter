#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import os
from pathlib import Path
from wikidumpfilter.languages import language_codes, get_unprocessed_languages


def make_links(args):
    # check io_dir
    current_dir_path = os.path.dirname(os.path.realpath(__file__))
    complete_dir_path = os.path.join(current_dir_path, args.output_dir)
    if not os.path.exists(args.output_dir):  # make output dir
        os.mkdir(complete_dir_path)

    # remove already linked files from list (=>manually delete files where you want to relink them)
    removed_languages = get_unprocessed_languages(args.output_dir, args.verbosity_level)

    # download
    num_of_downloads = 0
    max_num_of_downloads = len(language_codes)  # change this if you want only want to download the x biggest dumps
    print("Downloading the maximum allowed " + str(max_num_of_downloads) + " dumps of " + str(
        len(language_codes)) + " dumps not stored on disc.")
    if removed_languages > 0:
        print("An additional " + str(removed_languages) +
              "dumps are already on disc and thus won't be re-downloaded/updated. You may want to manually delete "
              "those to enable the download!")
    for lang in language_codes:
        # not downloading the multistream-file, since wikiFilter.py does not support multistream-files
        if args.multistream:
            dump_suffix = "wiki-latest-pages-articles-multistream.xml.bz2"
        else:
            dump_suffix = "wiki-latest-pages-articles.xml.bz2"

        src = str(Path(os.path.join(args.input_dir, lang + "wiki", "latest", lang + dump_suffix)).resolve().absolute())
        target = os.path.join(args.output_dir, lang + dump_suffix)
        os.symlink(src, target)
        print(src)
        if num_of_downloads > max_num_of_downloads:
            print(str(
                max_num_of_downloads) +
                  " files downloaded. Stopping download because the maximum allowed number has been reached!")
            break

    print("Downloaded " + str(num_of_downloads) + " files, while skipping " + str(removed_languages) +
          " already existing files(those might be outdated, so consider deleting them & running this program again!).")
