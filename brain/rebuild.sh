#!/usr/bin/env ksh

# $1 document dir
# $2 regex filter
# $3 doc for pipping

PPATH=`dirname $0`'/..'

# mongo db delete
printf "use pippi\ndb.miscdb.drop()\ndb.frags.drop()\ndb.docs.drop()\ndb.DocTexts.drop()\ndb.DocStems.drop()\ndb.DocTokens.drop()\ndb.pippies.drop()\nexit\n" | mongo


# load docs to pippify
(ls $1 | grep $3'' | ksh $PPATH/brain/bulkloaddoc.sh $2 2>>$PPATH/brain/bulk.err; cd -) 

# calculate/store tf-idf for processed docs
PYTHONPATH=$PPATH/../ DJANGO_SETTINGS_MODULE="lenx.settings" python $PPATH/brain/bulkidf.py
