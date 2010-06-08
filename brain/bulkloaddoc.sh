#!/usr/bin/env ksh
# $1 contains the doc do xpippi

batchsize=32
JOBMAX=4
tmpdir=/tmp/
PPATH=`dirname $0`'/..'

# clear batches
find ${tmpdir}/ -name 'job*' | xargs rm

# sed consumes stdin! oblig!
sed "/$1/d; s/^\(.*\)$/$1	\1/;" | split -d -a 8 -l ${batchsize} - ${tmpdir}/job

# count all jobs
totaljobs=$(find ${tmpdir} -name 'job*' |  wc -l)

# run all jobs
i=0
find ${tmpdir} -name 'job*' | while read batch; do
   (echo "starting batch: $i/${totaljobs} /${batch##${tmpdir}/}"
    if PYTHONPATH=$PPATH/../ DJANGO_SETTINGS_MODULE="lenx.settings" python $PPATH/brain/bulkpippy.py <"${batch}"; then
        echo "done $i/${totaljobs} ${batch##${tmpdir}/}"
        mv "${batch}" "${batch}.done"
    else
        echo "abort $i/${totaljobs} ${batch##${tmpdir}/}"
        mv "${batch}" "${batch}.error"
    fi ) &
   i=$((i+1))
   [[ -r $PPATH/brain/bulkpippies ]] && JOBMAX=$(cat $PPATH/brain/bulkpippies)
   sleep 3;
done
echo "${0##*/}: waiting for jobs to finish"
wait
