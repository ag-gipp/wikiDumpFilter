#!/usr/bin/python3
# -*- coding: utf-8 -*-
import argparse
import os
from pathlib import Path
from wikidumpfilter.constants import language_codes

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=''''Links all wiki-Dumps, except the ones already stored in the given directory (does not 
        include subdirectories). You may want to manually delete/move them if you want to reprocess them too.''',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input_dir',
                        help='The input directory name, where existing dumps are located.',
                        default='/public/dumps/public/', type=str)
    parser.add_argument('-o', '--output_dir',
                        help='The output directory name, where symbolic links will be created.',
                        default='/data/project/wdump/links/latest', type=str)
    parser.add_argument("-v", "--verbosity", action="count", default=0, dest='verbosity_level')
    parser.add_argument('-m', '--multistream', action="store_false")
    args = parser.parse_args()

    # check io_dir
    current_dir_path = os.path.dirname(os.path.realpath(__file__))
    complete_dir_path = os.path.join(current_dir_path, args.output_dir)
    if not os.path.exists(args.output_dir):  # make output dir
        os.mkdir(complete_dir_path)

    # remove already linked files from list (=>manually delete files where you want to relink them)
    removed_languages = 0
    for lang in language_codes:
        for root, directories, f_names in os.walk(args.output_dir):
            for filename in f_names:
                if filename.startswith(lang + "wiki") and filename.endswith(".bz2"):
                    language_codes.remove(lang)
                    removed_languages += 1
                    if args.verbosity_level > 0:
                        print("Skipping language " + lang + ", since " + filename + " already exists!")
            break  # don't search in subdirectories

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
        # try:
        #     t_start = time.perf_counter()
        #     (filename, headers) = urllib.request.urlretrieve(url, os.path.join(complete_dir_path, o_filename))
        #     print("Downloaded language: " + lang + " (" + str(os.stat(filename).st_size) + " bytes) in " + str(
        #         (time.perf_counter() - t_start) / 60) + " minutes.")
        #     sys.stdout.flush()  # unbuffered output => no need to manually call "python -u"
        #     num_of_downloads += 1
        # except Exception as e:
        #     print("Error with lang: " + lang)
        #     print(e)
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
