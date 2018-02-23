# Steps to Complete Export to FireCloud Feature

## BD2KGenomics/dcc-dashboard (this repo)

1. In app.py, whenever you log in, we are always requesting the
`https://www.googleapis.com/auth/devstorage.full_control` scope. That scope is currently required by FireCloud.
    1. Because of that privileged scope, you get an ugly `Proceed with Caution` when signing in with Google.
    2. FireCloud will be dropping the requirement for that scope in the near future.
    3. We can either wait for FireCloud to drop the requirement, in which case all we have to do
    is remove the scope, or we can go through an audit to avoid the dialog.
    4. If we do try to live with the current FC requirement, then we should also only request the 
    scope only when we need it, and not upon login.
2. Normally, the UI makes calls against the the dcc-dashboard-service, against APIs off of `/api/v1`
and `/repository` endpoints. But currently only dcc-dashboard can decode the session cookie and fetch the
user's information, including the access_token. So I added an endpoint in dcc-dashboard that the 
UI will invoke, `app.export_to_firecloud`, which gets the access_token and then makes a call to
dcc-dashboard-service. The other alternatives were to have a circular dependency between
dcc-dashboard and dcc-dashboard-service, or to copy code from dcc-dashboard to dcc-dashboard-service.
We should think about how we want to handle this, in particular if there is going to be more access
controlled data.
3. We are currently storing the Google access token. We need to also store the refresh token, and create
a new access token with the refresh token when needed.
4. Delete this file :) -- it shouldn't get merged into main branches.

## BD2KGenomics/dcc-dashboard-service

1. In webservice.py, need to implement bottom portion of `export_to_firecloud()`
2. Need to figure out what that method will return -- perhaps a JSON object
with the url of the just created FireCloud workspace.

## BD2KGenomics/boardwalk

1. Should at least indicate success or failure of the Export to FireCloud.
2. Depending on what is returned from dcc-dashboard-service, perhaps display a link to the FireCloud workspace.