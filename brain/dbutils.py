# django_bulk_save.py - defer saving of django models to bulk SQL commits.
# -------------------------------------------------------------------------
# Version: 1.0
# Date: 08/02/10 (8 Jan)
# Compatibility: Django 1.1, 1.1.1
# Author: Preet Kukreti
# -------------------------------------------------------------------------
# The general idea is to replace the inefficient idiom:
#
#   for m in model_list:
#       # modify m ...
#       m.save()   # ouch
# 
# with this one:
#   
#   from django_bulk_save import DeferredBucket
#   deferred = DeferredBucket()
#   for m in model_list:
#       # modify m ...
#       deferred.append(m)
#   deferred.bulk_save()
#
# DeferredBucket.bulk_save takes keyword arguments:
#   split_interval - number of SQL operations per commit (default=100)
#   verbose - print progress info (default=False)
# see also the save_sqlx and execute_sqlx functions for more granular control


# -------------------------------------------------------------------------
# The following section dynamically monkey patches some model and queryset
# django code to return SQL queries from model.save() instead of actually
# executing those queries. Searching for 'sqlx' will highlight the main changes

from django.db import connection, transaction, DatabaseError
from django.db.models import signals, sql
from django.db.models.fields import AutoField, FieldDoesNotExist
from django.db.models import query

def _update_sqlx(qs, values):
    """overrides QuerySet._update()"""
    assert qs.query.can_filter(), \
            "Cannot update a query once a slice has been taken."
    query = qs.query.clone(sql.UpdateQuery)
    query.add_update_fields(values)
    qs._result_cache = None
    return query.as_sql() # return SQL tuple


def _insert_sqlx(model, func, values, **kwargs):
    """overrides models.Manager._insert()"""
    return func(model, values, **kwargs)


def insert_query_sqlx(model, values, return_id=False, raw_values=False):
    """overrides insert_query() from models.query module"""
    query = sql.InsertQuery(model, connection)
    query.insert_values(values, raw_values)
    return query.as_sql() # return SQL tuple


def save_sqlx(obj, force_insert=False, force_update=False):
    """overrides model.save()"""
    if force_insert and force_update:
        raise ValueError("Cannot force both insert and updating in "
                "model saving.")
    return save_base_sqlx(obj, force_insert=force_insert, force_update=force_update)


def save_base_sqlx(obj, raw=False, cls=None, origin=None,
            force_insert=False, force_update=False):
    """overrides model.save_base()"""
    assert not (force_insert and force_update)
    if cls is None:
        cls = obj.__class__
        meta = cls._meta
        if not meta.proxy:
            origin = cls
    else:
        meta = cls._meta

    if origin:
        signals.pre_save.send(sender=origin, instance=obj, raw=raw)
        
    if not raw or meta.proxy:
        if meta.proxy:
            org = cls
        else:
            org = None
        for parent, field in meta.parents.items():

            if field and getattr(obj, parent._meta.pk.attname) is None and getattr(obj, field.attname) is not None:
                setattr(obj, parent._meta.pk.attname, getattr(obj, field.attname))

            obj.save_base(cls=parent, origin=org)

            if field:
                setattr(obj, field.attname, obj._get_pk_val(parent._meta))
        if meta.proxy:
            return

    if not meta.proxy:
        non_pks = [f for f in meta.local_fields if not f.primary_key]

        # First, try an UPDATE. If that doesn't update anything, do an INSERT.
        pk_val = obj._get_pk_val(meta)
        pk_set = pk_val is not None
        record_exists = True
        manager = cls._base_manager
        if pk_set:
            # Determine whether a record with the primary key already exists.
            if (force_update or (not force_insert and
                    manager.filter(pk=pk_val).extra(select={'a': 1}).values('a').order_by())):
                # It does already exist, so do an UPDATE.
                if force_update or non_pks:
                    values = [(f, None, (raw and getattr(obj, f.attname) or f.pre_save(obj, False))) for f in non_pks]
                    row_qs = manager.filter(pk=pk_val)
                    result = _update_sqlx(row_qs, values)
                    return result   # return SQL tuple
            else:
                record_exists = False
        if not pk_set or not record_exists:
            if not pk_set:
                if force_update:
                    raise ValueError("Cannot force an update in save() with no primary key.")
                values = [(f, f.get_db_prep_save(raw and getattr(obj, f.attname) or f.pre_save(obj, True))) for f in meta.local_fields if not isinstance(f, AutoField)]
            else:
                values = [(f, f.get_db_prep_save(raw and getattr(obj, f.attname) or f.pre_save(obj, True))) for f in meta.local_fields]

            if meta.order_with_respect_to:
                field = meta.order_with_respect_to
                values.append((meta.get_field_by_name('_order')[0], manager.filter(**{field.name: getattr(obj, field.attname)}).count()))
            record_exists = False

            update_pk = bool(meta.has_auto_field and not pk_set)
            manager._insert = _insert_sqlx
            if values:
                # Create a new record.
                result = manager._insert(obj, insert_query_sqlx, values, return_id=update_pk)
                return result   # return SQL tuple
            else:
                # Create a new record with defaults for everything.
                result = manager._insert(obj, insert_query_sqlx, [(meta.pk, connection.ops.pk_default_value())], return_id=update_pk, raw_values=True)
                return result   # return SQL tuple
            if update_pk:
                setattr(obj, meta.pk.attname, result)
        transaction.commit_unless_managed()

    if origin:
        signals.post_save.send(sender=origin, instance=obj,
            created=(not record_exists), raw=raw)
save_base_sqlx.alters_data = True

# --------------------------------------------------------------------------
import sys
def execute_sqlx(queries, split_interval=100, verbose=False, ostream=sys.stdout):
    '''
    executes <split_interval> queries at a time
    
    queries -- a list of query tuples (field_template, values)
    split_interval -- how many queries to commit at once
    verbose -- print progress info
    '''
    assert type(split_interval) == int
    if split_interval < 1:
        return
    from django.db import connection, transaction
    cursor = connection.cursor()
    current_pass = 1
    qlen = len(queries)
    if qlen == 0:
        if verbose:
            ostream.write('no queries\n')
        return
    more = True
    while more:
        low = (current_pass - 1) * split_interval
        high = (current_pass * split_interval) - 1
        if high >= qlen: # last pass, clamp high, break out
            high = qlen - 1
            more = False
        if verbose:
            ostream.write('executing SQL query %d to %d of %d ...' % (low + 1, high + 1, qlen)) 
        [cursor.execute(f, v) for f, v in queries[low:high+1]]
        transaction.commit_unless_managed()
        current_pass += 1
        if verbose:
            ostream.write('committed\n')
    return

# -------------------------------------------------------------------------
class DeferredBucket(list):
    '''
    helper for deferred saving. just append model instances that
    need deferred saving. When you want to finally save, call bulk_save.
    bulk_save takes the same keyword arguments as execute_sqlx
    '''
    def bulk_save(self, **kwargs):
        execute_sqlx([save_sqlx(i) for i in self], **kwargs)

# -------------------------------------------------------------------------

# -------------------------------------------------------------------------

from copy import deepcopy
from base64 import b64encode, b64decode
from zlib import compress, decompress
try:
    from cPickle import loads, dumps
except ImportError:
    from pickle import loads, dumps
from django.utils.encoding import force_unicode

"""Pickle field implementation for Django. src:http://github.com/shrubberysoft/django-picklefield"""

class PickledObject(str):
    """
A subclass of string so it can be told whether a string is a pickled
object or not (if the object is an instance of this class then it must
[well, should] be a pickled one).

Only really useful for passing pre-encoded values to ``default``
with ``dbsafe_encode``, not that doing so is necessary. If you
remove PickledObject and its references, you won't be able to pass
in pre-encoded values anymore, but you can always just pass in the
python objects themselves.

"""


def dbsafe_encode(value, compress_object=False):
    """
We use deepcopy() here to avoid a problem with cPickle, where dumps
can generate different character streams for same lookup value if
they are referenced differently.

The reason this is important is because we do all of our lookups as
simple string matches, thus the character streams must be the same
for the lookups to work properly. See tests.py for more information.
"""
    if not compress_object:
        value = b64encode(dumps(deepcopy(value)))
    else:
        value = b64encode(compress(dumps(deepcopy(value))))
    return PickledObject(value)


def dbsafe_decode(value, compress_object=False):
    if not compress_object:
        value = loads(b64decode(value))
    else:
        value = loads(decompress(b64decode(value)))
    return value


class PickledObjectField(models.Field):
    """
A field that will accept *any* python object and store it in the
database. PickledObjectField will optionally compress it's values if
declared with the keyword argument ``compress=True``.

Does not actually encode and compress ``None`` objects (although you
can still do lookups using None). This way, it is still possible to
use the ``isnull`` lookup type correctly. Because of this, the field
defaults to ``null=True``, as otherwise it wouldn't be able to store
None values since they aren't pickled and encoded.

"""
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        self.compress = kwargs.pop('compress', False)
        self.protocol = kwargs.pop('protocol', 2)
        kwargs.setdefault('null', True)
        kwargs.setdefault('editable', False)
        super(PickledObjectField, self).__init__(*args, **kwargs)

    def get_default(self):
        """
Returns the default value for this field.

The default implementation on models.Field calls force_unicode
on the default, which means you can't set arbitrary Python
objects as the default. To fix this, we just return the value
without calling force_unicode on it. Note that if you set a
callable as a default, the field will still call it. It will
*not* try to pickle and encode it.

"""
        if self.has_default():
            if callable(self.default):
                return self.default()
            return self.default
        # If the field doesn't have a default, then we punt to models.Field.
        return super(PickledObjectField, self).get_default()

    def to_python(self, value):
        """
B64decode and unpickle the object, optionally decompressing it.

If an error is raised in de-pickling and we're sure the value is
a definite pickle, the error is allowed to propogate. If we
aren't sure if the value is a pickle or not, then we catch the
error and return the original value instead.

"""
        if value is not None:
            try:
                value = dbsafe_decode(value, self.compress)
            except:
                # If the value is a definite pickle; and an error is raised in
                # de-pickling it should be allowed to propogate.
                if isinstance(value, PickledObject):
                    raise
        return value

    def get_db_prep_value(self, value):
        """
Pickle and b64encode the object, optionally compressing it.

The pickling protocol is specified explicitly (by default 2),
rather than as -1 or HIGHEST_PROTOCOL, because we don't want the
protocol to change over time. If it did, ``exact`` and ``in``
lookups would likely fail, since pickle would now be generating
a different string.

"""
        if value is not None and not isinstance(value, PickledObject):
            # We call force_unicode here explicitly, so that the encoded string
            # isn't rejected by the postgresql_psycopg2 backend. Alternatively,
            # we could have just registered PickledObject with the psycopg
            # marshaller (telling it to store it like it would a string), but
            # since both of these methods result in the same value being stored,
            # doing things this way is much easier.
            value = force_unicode(dbsafe_encode(value, self.compress))
        return value

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

    def get_internal_type(self):
        return 'TextField'

    def get_db_prep_lookup(self, lookup_type, value):
        if lookup_type not in ['exact', 'in', 'isnull']:
            raise TypeError('Lookup type %s is not supported.' % lookup_type)
        # The Field model already calls get_db_prep_value before doing the
        # actual lookup, so all we need to do is limit the lookup types.
        return super(PickledObjectField, self).get_db_prep_lookup(lookup_type, value)

# -------------------------------------------------------------------------

# -------------------------------------------------------------------------

class LockingManager(models.Manager):
    def lock(self):
        """ Lock table.

        Locks the object model table so that atomic update is possible.
        Simulatenous database access request pend until the lock is unlock()'ed.

        Note: If you need to lock multiple tables, you need to do lock them
        all in one SQL clause and this function is not enough. To avoid
        dead lock, all tables must be locked in the same order.

        See http://dev.mysql.com/doc/refman/5.0/en/lock-tables.html
        """
        cursor = connection.cursor()
        table = self.model._meta.db_table
        #logger.debug("Locking table %s" % table)
        cursor.execute("LOCK TABLES %s WRITE" % table)
        row = cursor.fetchone()
        return row

    def unlock(self):
        """ Unlock the table. """
        cursor = connection.cursor()
        table = self.model._meta.db_table
        cursor.execute("UNLOCK TABLES")
        row = cursor.fetchone()
        return row       

