#Do not confuse wikiFilter.py with http://wikifilter.sourceforge.net, these projects are completely unrelated to each other.
#credits go to https://github.com/physikerwelt/wikiFilter
#!/usr/bin/python
import os
import bz2
import argparse
import re
from sys import exit
import urllib2
from HTMLParser import HTMLParser

def get_titles_and_lang_from_QID(QIDs, languages=[]):
    '''Converts list of QIDs to a dictionary mapping language to it's corresponding titles, for all specified languages.
    If no languages are specified, all languages available for a QID will be included.
    Titles returned will be unescaped (e.g. "&#039;" becomes "'").
    Only gets titles for languages named "enwiki", "dewiki",...; does not work for "enwikiquote", "enwikibooks",...!'''

    def get_html_code(QID):
        '''returns html code from "https://www.wikidata.org/w/api.php?action=wbgetentities&format=xml&props=sitelinks&ids=" + QID'''
        def open_url(url):
            try:
                req = urllib2.Request(url)
                http_response_object = urllib2.urlopen(req)
                return http_response_object
            except Exception as e:
                print("Error with url: " + url)
                print(e)
                print()

        url = 'https://www.wikidata.org/w/api.php?action=wbgetentities&format=xml&props=sitelinks&ids=' + QID

        http_response_object = open_url(url)
        html_as_bytes = http_response_object.read() #type: bytes
        html = html_as_bytes.decode("utf8") #type: str

        return html

    lang_with_titles = {}
    for QID in QIDs:
        #search html code and look for titles
        html = get_html_code(QID)
        html = html.split("\n")
        for line in html:
            if "<sitelink site=" in line:
                wikis = re.findall('site=\"(.*?)\"', line)
                titles = re.findall('title=\"(.*?)\"', line)

                #exctract languages from wikis
                wiki_languages = []
                new_titles = [] #only includes titles from desired wikis
                for i, wiki in enumerate(wikis):
                    if wiki.endswith('wiki') == True:  #only matches wikis named "enwiki", "dewiki",...; does not match "enwikiquote", "enwikibooks",...!
                        wiki_languages.append(wiki[:-4])
                        new_titles.append(titles[i])
                titles = new_titles

                for language, title in zip(wiki_languages, titles):
                    if (language in languages) or languages == []: #languages == [] in case you want to get the titles of all languages
                        if lang_with_titles.get(language) == None:
                            lang_with_titles[language] = []
                        unescaped_title = HTMLParser().unescape(title) #unescapes title, e.g. "&#039;" becomes "'"
                        lang_with_titles[language].append(unescaped_title)

    return lang_with_titles

def process_user_input(keywords, keyword_file, QID_file, filenames, tags, output_dir):
    '''Process arguments given as user input. E.g. reads keyword file (if specified) or translates QIDs from QID_file to keywords.
    Also gives errors/notifications due to conflicting arguments given as input.
    Furthermore it checks if the output_files already exist, so they won't be overwritten.'''

    #check if filenames provided are bz2-files
    for filename in filenames:
        if filename.endswith(".bz2") == False:
            print("ERROR! Filename " + filename + " does not end with '.bz2'!")

    #notify user about possibly unwanted additional arguments
    if (keywords != [] and keyword_file != '') \
    or (keywords != [] and QID_file != '') \
    or (keyword_file != '' and QID_file != ''):
        print('You are specifying more than one option loading keywords! The keywords used will thus consist of all keywords provided.')

    #deal with empty keywords/tags, so they don't match every line
    if keywords == ['']:
        keywords = []
    if tags == ['']:
        tags = []

    #notify user about possibly forgotten arguments
    if (QID_file != '') and (tags != []):
        print("You provide a QID_file, while also providing tags! This is often not useful, since now pages containing a title (corresponding to the QID) OR a tag will be returned. Not AND. Is this really intentional?")

    #check if filenames include the languages-codes needed for translating QID to title
    languages = []
    if QID_file != '':
        for filename in filenames:
            if "wiki" in filename[2:]: #XXwiki exists in filename (where XX=language-code)
                file_language = filename.split("wiki")[0]
                languages.append(file_language)
            else:
                print("You need to rename your .bz2-files, so that they begin with XXwiki, where XX is the language code from https://meta.wikimedia.org/wiki/List_of_Wikipedias ! The first few letters of the name coincide with those from the original file name of the bz2-file you downloaded (unless the language code changed since then -> see the link if you think this might be the case).")
                print("Problematic filename: " + filename)
                exit("Exiting the program.")

    #load keywords from keyword_file
    if keyword_file != '':
        f = open(keyword_file, 'r')
        for line in f:
            line = line.replace("\n", "")
            keywords.append(line)

    #load QIDs from QID_file and convert them to keywords, saved in lang_with_titles(cannot be saved in "keywords", since they are language-specific)
    lang_with_titles = {} #dictionary mapping languages to titles; the titles will later be treated like normal keywords
    if QID_file != '':
        #read QIDs from file
        QIDs = []
        file = open(QID_file, 'r')
        for line in file:
            if re.match("^Q[1-9][0-9]*$", line) != None: #line consists of only a QID like "Q1234"
                line = line.replace("\n", "")
                QIDs.append(line)
            else:
                notify_user = True
                if args.verbosity_level > 1:
                    print("Line without QID: " + line)
        if notify_user == True:
            print("Skipped one or multiple lines while reading QID_file, since the line(s) didn't match the regex \"^Q[1-9][0-9]*$\"! This is probably your intention, thus the program will continue.")

        #convert QIDs to titles
        lang_with_titles = get_titles_and_lang_from_QID(QIDs, languages)
        #convert "some-title" to "<title>some-title</title>"
        for language in lang_with_titles.keys():
            lang_with_titles[language] = [ "<title>" + title + "</title>" for title in lang_with_titles[language] ]
        #remove unneeded languages (that don't have a single page with a requested QID)
        for empty_language in [l for l in languages if l not in lang_with_titles.keys()]:#iterate over every language without a found QID
            print("No titles found in language " + empty_language + " (maybe because the wiki is too small or there are just a few QIDs), thus the language will be removed from the used languages & filenames.")
            languages.remove(empty_language)
            #remove filename corresponding to the language
            for f in filenames:
                if f.split("wiki")[0] == empty_language:
                    filenames.remove(f)


    #check if output-files already exist, so they won't be overwritten and the input_file doesn't needlessly have to be processed again
    existing_files = []
    for root, directories, f_names in os.walk(output_dir):
        for filename in f_names:
            if filename.endswith(".bz2"):
                existing_files.append(filename)
        break
    for filename in filenames:
        if filename + " chunk-1.xml.bz2" in existing_files:
            filenames.remove(filename)
            print("File " + filename + " was already processed (thus '" +  filename + " chunk-1.xml.bz2' exists in the output directory " + output_dir + ") and will thus be not used!")

    if args.verbosity_level > 0:
        print("Using " + str(len(tags)) + " tags: " + str(tags))
        print("Using " + str(len(filenames)) + " files: " + str(filenames))
        print("Using " + str(len(keywords)) + " keywords(titles from QID_file not counted): " + str(keywords))
        if QID_file != '':
            print("Using " + str(len(languages)) + " languages: " + str(languages))
            for language in languages:
                titles_without_tags = [ title.split("<title>")[1].split("</title>")[0] for title in lang_with_titles[language] ]
                print(str(len(titles_without_tags)) + " titles in language " + language + " : " + str(titles_without_tags))

    return tags, keywords, languages, lang_with_titles, filenames

def split_xml(filename, splitsize, dir, tags, template, keywords):
    ''' The function gets the filename (e.g. "enwiki-latest-pages-articles.xml.bz2") as input and creates
    one (or multiple) chunks of splitsize in the given directory. The chunks consist of every page that has either
    one of the given keywords or one of the given tags in it.'''


    # Check and create chunk diretory
    if not os.path.exists(dir):
        os.mkdir(dir)
    # Counters
    pagecount = 0
    filecount = 1
    ismatch = -1
    header = ""
    footer = "</mediawiki>"
    tempstr = ""
    titles_found = []
    # open chunkfile in write mode
    chunkname = lambda filecount: os.path.join(dir, filename + " chunk-" + str(filecount) + ".xml.bz2")
    chunkfile = bz2.BZ2File(chunkname(filecount), 'w')
    # Read line by line
    bzfile = bz2.BZ2File(filename)

    # the header
    for line in bzfile:
        header += line
        if '</siteinfo>' in line:
            break
    if args.verbosity_level > 0:
        print(header)
    chunkfile.write(header)
    # and the rest
    for line in bzfile:
        try:
            line = line.decode("utf8") #probably faster to use python3 and specify encoding=utf8 in bz2.open()!  the bz2 module in python3 also supports multistreaming :)
        except:
            print("   Decoding-ERROR! In line: ", line)
        if '<page' in line:
            tempstr = ""
            ismatch = 0
        tempstr = tempstr + line
        if ismatch == 0: #no need to check for other matches, if ismatch=1
            for tag in tags:
                if ('&lt;/' + tag + '&gt;' in line): #does not search for opening tags, to keep things simple & fast. Otherwise we either only check "<math>", but miss "<math display=..."/"<math style=...>"/..., or we check "<math" and get "<math chem" too, even if we might not want to => regex and if-clauses would be needed to fix this.      On the other hand: Since "<math chem>"-tags get closing tag "</math>"(and we only check the closing tag here), "<math chem>" tags cannot be excluded with the current implementation, in case you ever need to! => If you need to: Use regex & if-clauses and program this differently.
                #searching for "</math>" misses ~10 "</math >" and ~3 misspelled closing tags in enwiki => you might want to search for "if </tag> or </tag > in line" to find ~10 more results(=>find more pages - IFF they don't include an already found tag and are thus already found!) at the cost of a slower program
                    if ismatch == 0: #only increase pagecount once per page (that has a match)
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
                if args.verbosity_level > 0:
                    #print progress every 1000th page
                    if (splitsize * (filecount-1) + pagecount-1) % 1000 == 0:
                        print(str(splitsize * (filecount-1) + pagecount) + "th page found in " + filename + ".")
        if pagecount > splitsize:
            if args.verbosity_level > 1:
                print("New bz2-file number " + pagecount + " since number of matched pages reached splitsize = " + splitsize)
            chunkfile.write(footer)
            chunkfile.close()
            pagecount = 0  #reset pagecount
            filecount += 1  #increment filename
            chunkfile = bz2.BZ2File(chunkname(filecount), 'w')
            chunkfile.write(header)
    try:
        chunkfile.write(footer)
        chunkfile.close()
        if splitsize * (filecount-1) + pagecount == 0:
            print("No pages found for file " + filename + "! Probably there are either too few keywords/tags searched for or the wiki is small.")
        elif args.verbosity_level > 0:
            print(str(splitsize * (filecount-1) + pagecount) + " pages found for file " + filename)
    except:
        print('File' + filename + ' is already closed.')

    #check if every title was found
    if len(titles_found) != len(keywords):
        print("Possible ERROR! Found " + str(len(titles_found)) + " titles of " + str(len(keywords)) + ". This should never happen (unless you use bz2-files that have been prefiltered (e.g. for pages with math-tags)) or use an old Dump(while filtering for QIDs corresponding to titles that changed meanwhile)!")
        print("   Titles found: " +  str(titles_found))
        print("   All titles: " + str(keywords))
        #check which titles were not found
        for title in keywords:
            if title not in titles_found:
                try:
                    print("   Title '" + title.encode('utf8') + "' was not found. This can happen e.g. if the Wikipedia page title changed(=you are using an old Dump file) or you used as input bz2-files where the pages without tags(e.g. <math>) are already filtered and this page does not contain a formula.")
                except Exception as e:
                    print(e)

if __name__ == '__main__':  # When the script is self run
    parser = argparse.ArgumentParser(description='Extract wikipages that contain the math tag.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-f', '--filename', help='The bz2-file(s) to be split and filtered. You may use one/multiple file(s) or e.g. "*.bz2" as input.',
        default='enwiki-latest-pages-articles.xml.bz2', dest='filenames', nargs='*')
    parser.add_argument('-s', '--splitsize', help='The number of pages contained in each split.',
        default=1000000, type=int, dest='size')
    parser.add_argument('-d', '--outputdir', help='The directory name where the files go.',
        default='wout', type=str, dest='dir')
    parser.add_argument('-t', '--tagname', help='Tags to search for, e.g. use    -t TAG1 TAG2 TAG3',
        default=['math','ce','chem','math chem'], type=str, dest='tags', nargs='*')
    parser.add_argument('-k', '--keyword', help='Keywords to search for, e.g. use    -k KEYWORD1 KEYWORD2 KEYWORD3   You might want to disable tags = specify empty tags (""), if you don`t want pages containing a tag OR a keyword!',
        default=[], type=str, dest='keywords', nargs='*')
    parser.add_argument('-K', '--keyword_file', help='Another way to specify keywords. Use a keyword file containing one keyword (e.g. "<title>formulae</title>") in each line.',
        default='', type=str, dest='keyword_file')
    parser.add_argument('-Q', '--QID_file', help='QID-file, containing one QID (e.g. "Q1234") in each line. They will be translated to the titles in their respective languages and "<title>SOME_TITLE</title>" will be used as keywords. Specify languages with "-l". The languages will be taken from the beginning of the filenames, which thus must start with "enwiki"/"dewiki"/... for english/german/... !',
        default='', type=str, dest='QID_file')
    parser.add_argument("-v", "--verbosity", action="count", default=0, dest='verbosity_level')
    parser.add_argument('-T', '--template', help='Include all templates.',
        action="store_true", dest='template')   #default=False
    args = parser.parse_args()

    tags, keywords, languages, lang_with_titles, filenames = process_user_input(args.keywords, args.keyword_file, args.QID_file, args.filenames, args.tags, args.dir)

    for filename in filenames:
        language = filename.split("wiki")[0]

        current_keywords = keywords[:]
        if args.QID_file != '':
            current_keywords += lang_with_titles[language] #add titles as keywords

        split_xml(filename, args.size, args.dir, tags, args.template, current_keywords)

#todo: Remove found titles from keywords to speed the program up ~2 times.
