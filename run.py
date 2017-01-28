from app import app
import os
port = int(os.environ['DCC_DASHBOARD_PORT']) if 'DCC_DASHBOARD_PORT' in os.environ else 5000
host = os.environ['DCC_DASHBOARD_HOST'] if 'DCC_DASHBOARD_HOST' in os.environ else '127.0.0.1'
app.run(debug=True, ssl_context=('./ssl.crt', './ssl.key'), port=port, host=host)
