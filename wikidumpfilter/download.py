#!/usr/bin/python3
# -*- coding: utf-8 -*-
import urllib.request
import os
import time
import sys

from wikidumpfilter.languages import language_codes, get_unprocessed_languages


def down(args):

    # check io_dir
    current_dir_path = os.path.dirname(os.path.realpath(__file__))
    complete_dir_path = os.path.join(current_dir_path, args.io_dir)
    if not os.path.exists(args.io_dir):  # make io_dir
        os.mkdir(complete_dir_path)

    # remove already downloaded files from download-list (=>manually delete files where you want newer dumps to be
    # downloaded!)
    removed_languages = get_unprocessed_languages(args.io_dir, args.verbosity_level)

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
        url = "https://dumps.wikimedia.org/" + lang + "wiki/latest/" + lang + dump_suffix
        o_filename = lang + dump_suffix
        try:
            t_start = time.perf_counter()
            (filename, headers) = urllib.request.urlretrieve(url, os.path.join(complete_dir_path, o_filename))
            print("Downloaded language: " + lang + " (" + str(os.stat(filename).st_size) + " bytes) in " + str(
                (time.perf_counter() - t_start) / 60) + " minutes.")
            sys.stdout.flush()  # unbuffered output => no need to manually call "python -u"
            num_of_downloads += 1
        except Exception as e:
            print("Error with lang: " + lang)
            print(e)
        if num_of_downloads > max_num_of_downloads:
            print(str(
                max_num_of_downloads) +
                  " files downloaded. Stopping download because the maximum allowed number has been reached!")
            break

    print("Downloaded " + str(num_of_downloads) + " files, while skipping " + str(
        removed_languages) +
          " already existing files(those might be outdated, so consider deleting them & running this program again!).")

# todo: check if download date of already existing file(s) < date of newest dump consider using a mirror for lower
#  load on the servers check MD5-checksums & re-download (only re-download once!) name the files according to the
#  date the dumps where created - helpful for documentation purposes, since the download link depends on this
