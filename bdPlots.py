#! /usr/bin/env python

from app import query_es_rna_seq
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from models import Burndown
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

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
bd_user = os.getenv('BD_POSTGRES_USER')
bd_password = os.getenv('BD_POSTGRES_PASSWORD')
bd_table = os.getenv('BD_POSTGRES_DB')
db_url = 'postgresql://{}:{}@bdchart-db/{}'.format(bd_user, bd_password,
                                                   bd_table)
engine = create_engine(db_url)
session = sessionmaker()
session.configure(bind=engine)
s = session()
s.add(plot)
s.commit() 
print s.query(Burndown).all()
print "Total Jobs: {} Finished Jobs: {}".format(total_jobs, finished_jobs)
print "Hello World"
