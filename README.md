# dcc-dashboard
The Core's web dashboard including a faceted file browser

## Dashboard

esquery.py will create an outfile called data.json. Add data.json along with the contents of the folder "Dashboard" to an AWS bucket and configure bucket according to the [AWS instructions on hosting a static website (steps 1, 2, and 3)] (http://docs.aws.amazon.com/gettingstarted/latest/swh/getting-started-create-bucket.html).

To see the Dashboard, from your bucket, go to Properties, Static Website Hosting, and click on the link following "Endpoint." This directs you to index.html, with a static streamgraph (uses data.csv). Using the navagation, hover over Projects, then click Project 1 to see a bar chart using data.json.

Alternatively, run the Dashboard locally. Add data.json to the Dashboard folder, start the python web server (see command below), and open http://localhost:8080 in your web browser:

    python -m SimpleHTTPServer 8080

## Demo

### populate dashboard

    cd Dashboard
    python dashboard_query.py

### populate file browser

    cd Dashboard
    python file_query.py
    # make sure the mappings are correct:
    curl -XGET 'http://localhost:9200/analysis_file_index/_mapping?pretty'
    # delete old data if needed
    curl -XDELETE http://localhost:9200/analysis_file_index
    # edit the mapping, see mappings.json and https://www.elastic.co/blog/found-elasticsearch-mapping-introduction
    curl -XPUT 'http://localhost:9200/analysis_file_index' -d @file_browser/mappings.json
    # now load this
    curl -XPUT http://localhost:9200/analysis_file_index/_bulk?pretty --data-binary @elasticsearch.jsonl
    # check it's in es
    curl -XGET http://localhost:9200/analysis_file_index/_search?pretty

### run file browser

    python -m SimpleHTTPServer 8000

### CORS

You may need to do the following to get cross-site scripting working:  http://www.oodlestechnologies.com/blogs/How-to-solve-No-Access-Control-Allow-Origin-with-elastic-search
