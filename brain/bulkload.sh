#!/usr/bin/env ksh

batchsize=32
JOBMAX=20
tmpdir=/var/pippi0/lenx/tmp

# clear batches
find ${tmpdir}/ -name 'job*' | xargs rm 

# bulkproducer consumes stdin! oblig!
./bulkproducer.py 0 1 | split -d -a 8 -l ${batchsize} - ${tmpdir}/job

# count all jobs
totaljobs=$(find ${tmpdir} -name 'job*' |  wc -l)

# run all jobs
i=0
find ${tmpdir} -name 'job*' | while read batch; do
   (echo "starting batch: ${batch##${tmpdir}/job}"
    if PYTHONPATH=/usr/local/home/stef/ DJANGO_SETTINGS_MODULE="lenx.settings" python bulkpippy.py <"${batch}"; then
        echo "done $i/${totaljobs} ${batch##${tmpdir}/}" 
    else
        echo "abort $i/${totaljobs} ${batch##${tmpdir}/}"
    fi ) &
   i=$((i+1))
   [[ -r ./bulkpippies ]] && JOBMAX=$(cat ./bulkpippies)
done
