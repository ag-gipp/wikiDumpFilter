#!/usr/bin/python3
# -*- coding: utf-8 -*-
import bz2
import os
import re
from os import path
from sys import exit

from wikidumpfilter.qid2title import get_titles_and_lang_from_qid


def process_user_input(keywords, keyword_file, QID_file, filenames, tags, output_dir, args):
    """Process arguments given as user input. E.g. reads keyword file (if specified) or translates QIDs from QID_file
    to keywords. Also gives errors/notifications due to conflicting arguments given as input. Furthermore it checks
    if the output_files already exist, so they won't be overwritten. """

    # check if filenames provided are bz2-files
    for fn in filenames:
        if not fn.endswith(".bz2"):
            print("ERROR! Filename " + fn + " does not end with '.bz2'!")

    # notify user about possibly unwanted additional arguments
    if (keywords != [] and keyword_file != '') \
            or (keywords != [] and QID_file != '') \
            or (keyword_file != '' and QID_file != ''):
        print('You are specifying more than one option loading keywords! The keywords used will thus consist of all '
              'keywords provided.')

        # deal with empty keywords/tags, so they don't match every line
    if keywords == ['']:
        keywords = []
    if tags == ['']:
        tags = []

    # notify user about possibly forgotten arguments
    if (QID_file != '') and (tags != []):
        print("You provide a QID_file, while also providing tags! This is often not useful, since now pages "
              "containing a title (corresponding to the QID) OR a tag will be returned. Not AND. Is this really "
              "intentional?")

        # check if filenames include the languages-codes needed for translating QID to title
    languages = []
    if QID_file != '':
        for fn in filenames:
            if "wiki" in fn[2:]:  # XXwiki exists in filename (where XX=language-code)
                file_language = fn.split("wiki")[0]
                languages.append(file_language)
            else:
                print("You need to rename your .bz2-files, so that they begin with XXwiki, where XX is the language "
                      "code from https://meta.wikimedia.org/wiki/List_of_Wikipedias ! The first few letters of the "
                      "name coincide with those from the original file name of the bz2-file you downloaded (unless "
                      "the language code changed since then -> see the link if you think this might be the case).")
                print("Problematic filename: " + fn)
                exit("Exiting the program.")

    # load keywords from keyword_file
    if keyword_file != '':
        f = open(keyword_file, 'r')
        for line in f:
            line = line.replace("\n", "")
            keywords.append(line)

    # load QIDs from QID_file and convert them to keywords, saved in lang_with_titles(cannot be saved in "keywords",
    # since they are language-specific)
    lang_with_titles = {}  # dictionary mapping languages to titles; the titles will later be treated like normal
    # keywords
    if QID_file != '':
        # read QIDs from file
        QIDs = []
        file = open(QID_file, 'r')
        for line in file:
            if re.match("^Q[1-9][0-9]*$", line) is not None:  # line consists of only a QID like "Q1234"
                line = line.replace("\n", "")
                QIDs.append(line)
            else:
                notify_user = True
                if args > 1:
                    print("Line without QID: " + line)
        if notify_user:
            print("Skipped one or multiple lines while reading QID_file, since the line(s) didn't match the regex "
                  "\"^Q[1-9][0-9]*$\"! This is probably your intention, thus the program will continue.")

            # convert QIDs to titles
        lang_with_titles = get_titles_and_lang_from_qid(QIDs, languages)
        # convert "some-title" to "<title>some-title</title>"
        for language in lang_with_titles.keys():
            lang_with_titles[language] = ["<title>" + title + "</title>" for title in lang_with_titles[language]]
        # remove unneeded languages (that don't have a single page with a requested QID)
        for empty_language in [l for l in languages if
                               l not in lang_with_titles.keys()]:  # iterate over every language without a found QID
            print("No titles found in language " + empty_language +
                  "(maybe because the wiki is too small or there are just a few QIDs), thus the language will be "
                  "removed from the used languages & filenames.")
            languages.remove(empty_language)
            # remove filename corresponding to the language
            for f in filenames:
                if f.split("wiki")[0] == empty_language:
                    filenames.remove(f)

    # check if output-files already exist, so they won't be overwritten and the input_file doesn't needlessly have to
    # be processed again
    existing_files = []
    for root, directories, f_names in os.walk(output_dir):
        for fn in f_names:
            if fn.endswith(".bz2"):
                existing_files.append(fn)
        break
    for fn in filenames:
        if fn + " chunk-1.xml.bz2" in existing_files:
            filenames.remove(fn)
            print("File " + fn + " was already processed (thus '" + fn +
                  " chunk-1.xml.bz2' exists in the output directory " + output_dir + ") and will thus be not used!")

    if args > 0:
        print("Using " + str(len(tags)) + " tags: " + str(tags))
        print("Using " + str(len(filenames)) + " files: " + str(filenames))
        print("Using " + str(len(keywords)) + " keywords(titles from QID_file not counted): " + str(keywords))
        if QID_file != '':
            print("Using " + str(len(languages)) + " languages: " + str(languages))
            for language in languages:
                titles_without_tags = [title.split("<title>")[1].split("</title>")[0] for title in
                                       lang_with_titles[language]]
                print(str(len(titles_without_tags)) + " titles in language " + language + " : " + str(
                    titles_without_tags))

    return tags, keywords, languages, lang_with_titles, filenames


def split_xml(filename, splitsize, dir, tags, template, keywords, args):
    """ The function gets the filename (e.g. "enwiki-latest-pages-articles.xml.bz2") as input and creates
    one (or multiple) chunks of splitsize in the given directory. The chunks consist of every page that has either
    one of the given keywords or one of the given tags in it."""

    if not os.path.isfile(filename):
        print("File %s does not exist." % filename)
        return
    # Check and create chunk diretory
    if not os.path.exists(dir):
        os.mkdir(dir)
    # Counters
    pagecount = 0
    filecount = 1
    ismatch = -1
    header = ""
    footer = b"</mediawiki>"
    tempstr = ""
    titles_found = []
    # open chunkfile in write mode
    chunkname = lambda filecount: os.path.join(dir, path.basename(filename) + "-chunk-" + str(filecount) + ".xml.bz2")
    chunkfile = bz2.BZ2File(chunkname(filecount), 'w')
    # Read line by line
    bzfile = bz2.BZ2File(filename)

    # the header
    for line in bzfile:
        line = line.decode('utf-8')
        header += line
        if '</siteinfo>' in line:
            break
    if args > 0:
        print(header)
    chunkfile.write(header.encode('utf-8'))
    # and the rest
    for line in bz2.open(filename, mode='rt', encoding='utf-8'):
        if '<page' in line:
            tempstr = ""
            ismatch = 0
        tempstr = tempstr + line
        if ismatch == 0:  # no need to check for other matches, if ismatch=1
            for tag in tags:
                # does not search for opening tags, to keep things simple & fast. Otherwise we either only check
                # "<math>", but miss "<math display=..."/"<math style=...>"/..., or we check "<math" and get
                # "<math chem" too, even if we might not want to => regex and if-clauses would be needed to fix
                # this. On the other hand: Since "<math chem>"-tags get closing tag "</math>"(and we only
                # check the closing tag here), "<math chem>" tags cannot be excluded with the current
                # implementation, in case you ever need to! => If you need to: Use regex & if-clauses and program
                # this differently. searching for "</math>" misses ~10 "</math >" and ~3 misspelled closing tags
                # in enwiki => you might want to search for "if </tag> or </tag > in line" to find ~10 more
                # results(=>find more pages - IFF they don't include an already found tag and are thus already
                # found!) at the cost of a slower program
                if '&lt;/' + tag + '&gt;' in line:
                    if ismatch == 0:  # only increase pagecount once per page (that has a match)
                        pagecount += 1
                    ismatch = 1

            for keyword in keywords:
                if keyword in line:
                    if ismatch == 0:
                        pagecount += 1
                        titles_found.append(keyword)
                    ismatch = 1

            if template and ('<ns>10</ns>' in line or '<ns>828</ns>' in line):
                if ismatch == 0:
                    pagecount += 1
                ismatch = 1
                print('template')
        if '</page>' in line:
            if ismatch == 1:
                tempstr = tempstr.encode("utf8")
                chunkfile.write(tempstr)
                tempstr = ""
                if args > 0:
                    # print progress every 1000th page
                    if (splitsize * (filecount - 1) + pagecount - 1) % 1000 == 0:
                        print(str(splitsize * (filecount - 1) + pagecount) + "th page found in " + filename + ".")
        if pagecount > splitsize:
            if args > 1:
                print(
                    "New bz2-file number " + pagecount + " since number of matched pages reached splitsize = " + splitsize)
            chunkfile.write(footer)
            chunkfile.close()
            pagecount = 0  # reset pagecount
            filecount += 1  # increment filename
            chunkfile = bz2.BZ2File(chunkname(filecount), 'w')
            chunkfile.write(header)

    if pagecount <= splitsize:
        chunkfile.write(footer)
        chunkfile.close()
    if splitsize * (filecount - 1) + pagecount == 0:
        print("No pages found for file " + filename +
              "! Probably there are either too few keywords/tags searched for or the wiki is small.")
    elif args > 0:
        print(str(splitsize * (filecount - 1) + pagecount) + " pages found for file " + filename)

    # check if every title was found
    if len(titles_found) != len(keywords):
        print("Possible ERROR! Found " + str(len(titles_found)) + " titles of " + str(len(keywords)) +
              ". This should never happen (unless you use bz2-files that have been prefiltered (e.g. for pages with "
              "math-tags)) or use an old Dump(while filtering for QIDs corresponding to titles that changed "
              "meanwhile)!")
        print("   Titles found: " + str(titles_found))
        print("   All titles: " + str(keywords))
        # check which titles were not found
        for title in keywords:
            if title not in titles_found:
                try:
                    print("   Title '" + title.encode('utf8') +
                          "' was not found. This can happen e.g. if the Wikipedia page title changed(=you are using "
                          "an old Dump file) or you used as input bz2-files where the pages without tags(e.g. <math>) "
                          "are already filtered and this page does not contain a formula.")
                except Exception as e:
                    print(e)

# todo: Remove found titles from keywords to speed the program up ~2 times.
