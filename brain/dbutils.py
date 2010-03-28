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

