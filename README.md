# dcc-dashboard
The Core's web dashboard including a faceted file browser

This iteration of the File Browser uses the web API from https://github.com/BD2KGenomics/dcc-dashboard-service

## Set up the web API
Follow the directions on https://github.com/BD2KGenomics/dcc-dashboard-service. 
   
## Locally run the Dashboard for Testing Purposes Only
Create a local host

      python -m SimpleHTTPServer 8080

Open index.html on a web browser, click on File Browser
If results are not showing, be sure to allow CORS (cross-origin-resource-sharing)

## Installing the Dashboard on an Apache Server for Production
<b>Note:</b> This assumes you have already installed the web-service and Apache. See https://github.com/BD2KGenomics/dcc-dashboard-service for instructions on how to do this. Then come back here and follow the instructions below.

Clone the repository in the root directory, by doing: 
```
git clone https://github.com/BD2KGenomics/dcc-dashboard.git
```
Make the soft link: 
```
sudo ln -sT ~/dcc-dashboard-service /var/www/html/dcc-dashboard
```

Go to the `/etc/apache2/sites-enabled/000-default.conf` file and add `DocumentRoot /var/www/html/dcc-dashboard` under `ServerAdmin webmaster@localhost`, like this:

```
<VirtualHost *:80>
	#Change as appropriate
        ServerName your-server-name.com 
        Header set Access-Control-Allow-Origin "*"
	#Change as appropriate
        ServerAdmin webmaster@localhost
        DocumentRoot /var/www/html/dcc-dashboard

        WSGIDaemonProcess dcc-dashboard-service threads=5
        WSGIScriptAlias /api/v1 /var/www/html/dcc-dashboard-service/dcc-dashboard-service.wsgi
        <Directory dcc-dashboard-service>
                 WSGIProcessGroup dcc-dashboard-service
                 WSGIApplicationGroup %{GLOBAL}
                 Order deny,allow
                 Allow from all
        </Directory>
        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```
Restart the apache server by doing: 
```
sudo apachectl restart
```




