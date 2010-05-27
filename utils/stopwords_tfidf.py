#!/usr/bin/env python

import sys
import os
from BeautifulSoup import BeautifulSoup
from lenx.utils.tfidf import TfIdf
from lenx.brain import hunspell # get pyhunspell here: http://code.google.com/p/pyhunspell/
from lenx import settings
import nltk.tokenize # get this from http://www.nltk.org/
from optparse import OptionParser

LANG='en_US'
DICT=settings.DICT_PATH+'/'+LANG
VERSION = '0.1'
BASEDIR='.'
CORPUS_FILE = BASEDIR+'/sw_corpus.file'
STOPWORDS_FILE = BASEDIR+'/sw_sw.file'
D = hunspell.HunSpell(DICT+'.dic', DICT+'.aff')

def quit(ret, s=''):
    print "[!] Error!\n\t%s" % s
    sys.exit(ret)

def findShortest(lst):
    length = len(lst)
    short = len(lst[0])
    ret = 0
    for x in range(1, length):
        if len(lst[x]) < short:
            short = len(lst[x])
            ret = x
    return lst[ret] # return the index of the shortest sentence in the list

def getHTMLContent(f):
    stems=[]
    c = open(f)
    t = BeautifulSoup("\n".join(c.readlines())).find(id='TexteOnly')
    if not t:
        print "[!] Warning, \n\tMissing content in %s" % f
        return []
    text = t.findAll(text=True)
    words = [x for x in nltk.tokenize.wordpunct_tokenize(''.join(text)) if x.isalpha()]
    c.close()
    # TexteOnly is the id used on eur-lex pages containing distinct docs
    for word in words:
        # stem each word and count the results
        stem=D.stem(word.encode('utf8'))
        if len(stem):
            stems.append(stem[0])
    return stems

class Corpus():
    def __init__(self):
        self.tfidf = TfIdf(CORPUS_FILE, DEFAULT_IDF=1.0)
    
    def parseDir(self, d, tag='TexteOnly'):
        if not os.path.isdir(d):
            return False
        i=0
        for f in os.listdir(d):
            i+=1
            stems = getHTMLContent("%s/%s" % (d,f))
            if stems:
                self.add(' '.join(stems))
                print '[!] Doc(%d): %s' % (i, f)
                print ' '.join(stems[:20])
                print '_'*100
        self.save()
        return True

    def add(self, s):
        self.tfidf.add_input_document(s)

    def save(self):
        self.tfidf.save_corpus_to_file(CORPUS_FILE, STOPWORDS_FILE, STOPWORD_PERCENTAGE_THRESHOLD = 1.0)

class WordScore():
    def __init__(self):
        self.tfidf = TfIdf(CORPUS_FILE, DEFAULT_IDF=1.0)

    # not tested
    def remove_input_document(self, input):
        self.tfidf.num_docs -= 1
        words = set(self.tfidf.get_tokens(input))
        for word in words:
            if word in self.tfidf.term_num_docs:
                if self.tfidf.term_num_docs[word] == 1:
                    self.tfidf.term_num_docs.pop(word)
                else:
                    self.tfidf.term_num_docs[word] -= 1

    def get(self, f, inCorpus=True):
        stems = getHTMLContent(f)
        for i in self.tfidf.get_doc_keywords(' '.join(getHTMLContent(f))):
            print i

def main():
    usage = "usage: %prog [options] (file|directory)"
    parser = OptionParser(usage=usage, version=("%%prog %s" % VERSION))
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose")
    parser.add_option("-m", "--mode", dest="mode",
                      help="set mode [CORPUS, DOC, LIST]", default='DOC')
    (options, args) = parser.parse_args()
    if len(args) != 1:
        quit(1)
    if options.mode == 'DOC':
        print "[!] DOC: %s" % args[0]
        # createTfIdf().getKeywords('guitar')
    elif options.mode == 'CORPUS':
        print "[!] CORPUS: %s" % args[0]
        print Corpus().parseDir(args[0])
    elif options.mode == 'IDF':
        print "[!] IDF: %s" % args[0]
        WordScore().get(args[0])


if __name__ == "__main__":
    main()
