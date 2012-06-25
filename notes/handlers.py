from piston.handler import BaseHandler, AnonymousBaseHandler
from piston.utils import rc, throttle
import pymongo, json
from bson.objectid import ObjectId
from urllib import unquote

conn = pymongo.Connection()
db=conn.pippi
Notes=db.notes

class AnnotationHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT', 'DELETE', 'POST')
    anonymous = AnonymousBaseHandler()

    def read(self, request, id):
        note = Notes.find_one({'_id': ObjectId(id)})
        if not note: return rc.NOT_FOUND

    #@throttle(5, 10*60) # allow 5 times in 10 minutes
    def update(self, request, id):
        note = Notes.find_one({'_id': ObjectId(id)})
        if not request.user.is_authenticated() or str(request.user)!=note['user']:
            return rc.FORBIDDEN

        note.update(request.data)
        Notes.save(note)

        return dict([(k,v) if k!='_id' else ('id',v) for k,v in note.items()])

    def delete(self, request, id):
        note = Notes.find_one({'_id': ObjectId(id)})

        if not request.user.is_authenticated() or str(request.user)!=note.get('user',''):
            return rc.FORBIDDEN

        Notes.remove({'_id': ObjectId(id)})

        return rc.DELETED # returns HTTP 204

    def create(self, request):
        if not request.user.is_authenticated():
            return rc.FORBIDDEN
        request.data['user']=str(request.user)
        Notes.save(request.data)

        return dict([(k,v) if k!='_id' else ('id',v) for k,v in request.data.items()])

class AnonymousAnnotationHandler(AnonymousBaseHandler):
    allowed_methods = ('GET',)

class SearchHandler(AnonymousBaseHandler):
    allowed_methods = ('GET',)

    def read(self, request):
        non_query_args = ['offset', 'limit', 'all_fields']
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 20))
        query=dict([(k,unquote(v)) for k,v in request.GET.items() if not k in non_query_args])
        notes = Notes.find(query).limit(limit).skip(offset) #.sort([(, pymongo.DESCENDING if orderDesc else pymongo.ASCENDING)])

        return {'rows': [dict([(k,v) if k!='_id' else ('id',v) for k,v in item.items()]) for item in notes],
                'total': notes.count()}
