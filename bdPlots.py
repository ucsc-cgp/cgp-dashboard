#! /usr/bin/env python

from app import query_es_rna_seq
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from models import Burndown
import os
from sqlalchemy.orm import session

es_service = os.environ.get("ES_SERVICE", "localhost")
es = Elasticsearch(['http://'+es_service+':9200/'])

# Query the coordinates from ES
software = "[Ss]pinnaker"
myQuery = [("regexp", "experimentalStrategy", "[rR][nN][aA][-][Ss][Ee][Qq]"),
           ("regexp", "software", software)]
total_jobs = query_es_rna_seq(es, 'burn_idx', myQuery, "repoDataBundleId")
software = "quay.io\/ucsc_cgl\/rnaseq-cgl-pipeline"
finished_jobs = query_es_rna_seq(es, 'burn_idx', myQuery, "repoDataBundleId")
# Create the plot point
plot = Burndown(total_jobs=total_jobs, finished_jobs=finished_jobs)
# Enter the plot point in the table
s = session()
s.add(plot)
s.commit() 
print s.query(Burndown).all()
print "Total Jobs: {} Finished Jobs: {}".format(total_jobs, finished_jobs)
print "Hello World"
