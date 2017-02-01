"""
Python bindings for the Bill.com REST API, which is documented here:

http://developer.bill.com/api-documentation/overview/

Please contact developer@finoptimal.com with questions or comments.
"""

import json, requests

class BDCSession(object):
    """
    A session consitutes work on a single organization using a single set of
     login and api credentials.
    """
    
    BASE_URL = "https://api.bill.com/api/v2"
    HEADERS  = {'content-type': 'application/x-www-form-urlencoded'}
    
    def __init__(self, username, password, api_key,
                 organization_id=None, verbosity=0):    
        """
        You can't do much without an organization_id, but you can find out which
         organizations are available to you.
        
        Increased verbosity will, as it's name implies, make the session more
        communicative, or annoying, as the case may be. Season to taste.
        """
        self.un = username
        self.pw = password
        self.ak = api_key
        self.oi = organization_id
        self.vb = verbosity
        
        self._setup()

    def _setup(self):
        self.si = self.session_id      = None
        
        if not self.oi:
            orgs = self._call("ListOrgs", data=dict(
                userName=self.un, password=self.pw))
            if len(orgs) == 1:
                self.oi = self.oi = orgs[0]["orgId"]
                print "{} ({}) is {}'s only organization, so".format(
                    orgs[0]["orgName"], self.oi, self.un), "logging into that."
                # Now that we've set oi...
                self._setup()
            else:
                print "{}'s available BDC Organizations:".format(self.un)
                print json.dumps(orgs, indent=4)
                quit()
                
        else:
            rd = self._call("Login", data=dict(
                userName=self.un, password=self.pw, orgId=self.oi))
            self.si = self.session_id = rd["sessionId"]

            if self.vb > 2:
                print "Successfully logged into orgId {}.".format(self.oi)

        if not self.si:
            raise Exception("Not logged into BDC.")
        
    def _call(self, url_tail, data=None, suppress_errors=False, **params):
        """
        This is a generic wrapper around the requests module, intended to take
         the basic requirements from the caller, and return what the caller 
         really wants, which is the response data as a dictionary.

        # TO DO: add retry logic as sometimes a little persistence is required
        """
        if not data:
            data = {}

        data["devKey"] = self.ak
        
        if not url_tail in ["Login", "ListOrgs"]:
            # This goes in every call except these two excluded ones
            # For those two, more sensitive data is packed into the request
            #  body via the data parameter.
            data["sessionId"] = self.si            

        data.update({"data" : json.dumps(params)})
            
        full_url  = "{}/{}.json".format(self.BASE_URL, url_tail)

        resp      = requests.post(
            full_url, headers=self.HEADERS, data=data)

        rj        = response_json = resp.json()

        if self.vb > 5:
            print json.dumps(rj, indent=4)

        if not rj["response_message"] == "Success":
            if not suppress_errors:
                print json.dumps(rj, indent=4)
                
        rd        = response_data = rj["response_data"]

        return rd

    def logout(self):
        resp = self._call("Logout")

        if self.vb > 2:
            print "Successfully logged out of orgId {}.".format(self.oi)

    def _crud(self, operation, object_type, **params):
        """
        available CRUD(U) operations include "create", "read", "update", 
         "delete", and "undelete". params are required for "create" and 
         "update", and forbidden for everything else.

        While operation is case-insensitive, object_type is NOT.
        """
        url_tail = "Crud/{}/{}".format(operation.title(), object_type)
        return self._call(url_tail, **params)

    def create(self, object_type, **params):
        """
        Remember to put your object into a single-item dictionary with key "obj"
        """
        return self._crud("Create", object_type, **params)

    def read(self, object_type, object_id):
        return self._crud("Read", object_type, id=object_id)

    def update(self, object_type, object_id=None, **params):
        """
        While the object_id param will ultimately get mixed in with the other
         params, it's more parallel with other crud function signatures to have
         it as a separate arg rather than in kwargs...design choice.
        
        Remember to put your object into a single-item dictionary with key "obj"
        """
        params_id = params.get("obj", {}).get("id")
        if params_id:
            # we don't want to effectively pass in two id params
            object_id = None
        return self._crud("Update", object_type, id=object_id, **params)

    def delete(self, object_type, object_id):
        return self._crud("Delete", object_type, id=object_id)

    def undelete(self, object_type, object_id):
        return self._crud("Undelete", object_type, id=object_id)

    def list(self, object_type, start=0, max=999, filters=None, sort=None,
             suppress_errors=False):
        """
        http://developer.bill.com/api-documentation/api/list

        Yes, I know, the collision of api endpoint "list" and parameter "max"
         with those reserved Python words is annoying when they get colored by 
         emacs et al. Sorry...it seemed more important to mirror the endpoints.
        """
        return self._call("List/{}".format(
            object_type), start=start, max=max, filters=filters, sort=sort,
                          suppress_errors=suppress_errors)

    def current_time(self):
        """
        Sometimes it's useful to know what time the API thinks it currently is.
        """
        return self._call("CurrentTime")["currentTime"]
