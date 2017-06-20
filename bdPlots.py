#! /usr/bin/env python

from app import query_es_rna_seq
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from models import Burndown, get_all
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

es_service = os.environ.get("ES_SERVICE", "localhost")
es = Elasticsearch(['http://'+es_service+':9200/'])

# Query the coordinates from ES
myQuery = [("regexp", "experimentalStrategy", "[rR][nN][aA][-][Ss][Ee][Qq]"),
           ("regexp", "software", "[Ss]pinnaker")]
total_jobs = query_es_rna_seq(es, 'burn_idx', myQuery, "repoDataBundleId")
myQuery = [("regexp", "experimentalStrategy", "[rR][nN][aA][-][Ss][Ee][Qq]"),
           ("regexp", "software", "quay.io\/ucsc_cgl\/rnaseq-cgl-pipeline")]
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
# Delete old entries
old_entries = datetime.today().replace(second=0, microsecond=0) - timedelta(minutes=4) #CHANGE TO PER HOUR
s.query(Burndown).filter(Burndown.captured_date <= old_entries).delete()
# Commit Changes to the DB
s.commit()
print [(str(x.total_jobs), str(x.finished_jobs), x.captured_date, "{}:{}".format(x.captured_date.hour, x.captured_date.minute)) for x in get_all()]
print "Total Jobs: {} Finished Jobs: {}".format(total_jobs, finished_jobs)
print "Hello World"
