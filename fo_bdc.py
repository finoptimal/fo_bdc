"""
Python bindings for the Bill.com REST API.

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
        self.un = self.username        = username
        self.pw = self.password        = password
        self.ak = self.api_key         = api_key
        self.oi = self.organization_id = organization_id
        self.vb = self.verbosity       = verbosity
        
        self._setup()

    def _setup(self):
        if not self.organization_id:
            resp = self.call("ListOrgs")
            print resp
            import ipdb;ipdb.set_trace()
            
        else:
            resp = self.call("Login", devKey=self.organization_id)
            print resp
            import ipdb;ipdb.set_trace()

    def logout(self):
        resp = self.call("Logout")
        print resp
        import ipdb;ipdb.set_trace()

    def call(self, url_tail, data=None, **params):
        if not data:
            data  = {}
        data_json = json.dumps(data)
        full_url  = "{}/{}.json".format(self.BASE_URL, url_tail)
        resp      = requests.post(
            full_url, headers=self.HEADERS, params=params, data=data_json)

        import ipdb;ipdb.set_trace()
