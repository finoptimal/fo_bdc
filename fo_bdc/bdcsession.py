# Python bindings for the Bill.com REST API, which is documented here:
#  http://developer.bill.com/api-documentation/overview/

# Please contact developer@finoptimal.com with questions or comments.

from base64      import b64encode

import copy, json, os, requests

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
                print("{} ({}) is {}'s only organization, so".format(
                    orgs[0]["orgName"], self.oi, self.un), "logging into that.")
                # Now that we've set oi...
                self._setup()
            else:
                print("{}'s available BDC Organizations:".format(self.un))
                print(json.dumps(orgs, indent=4))
                quit()
                
        else:
            rd = self._call("Login", data=dict(
                userName=self.un, password=self.pw, orgId=self.oi))
            self.si = self.session_id = rd["sessionId"]

            if self.vb > 7:
                print("Successfully logged into orgId {}.".format(self.oi))

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

        # We just put all the params in the request body...
        data.update({"data" : json.dumps(params)})
            
        full_url  = "{}/{}.json".format(self.BASE_URL, url_tail)

        resp  = requests.post(full_url, headers=self.HEADERS, data=data)

        # Response Json
        rj = resp.json()

        if self.vb > 7:
            print(json.dumps(rj, indent=4))

        if not rj["response_message"] == "Success":
            if not suppress_errors and self.vb > 0:
                print(json.dumps(rj, indent=4))
            if self.vb > 5:
                print("Inspect full_url, data, rj:")
                import ipdb;ipdb.set_trace()        

        # For troubleshooting...
        self.last_response = rj.copy()
                
        # Response Data
        rd = rj["response_data"]

        return rd

    def logout(self):
        resp = self._call("Logout")

        if self.vb > 7:
            print("Successfully logged out of orgId {}.".format(self.oi))

    def _crud(self, operation, object_type, **params):
        """
        available CRUD(U) operations include "create", "read", "update", 
         "delete", and "undelete". params are required for "create" and 
         "update", and forbidden for everything else.

        While operation is case-insensitive, object_type is NOT.
        """
        url_tail = "Crud/{}/{}".format(operation.title(), object_type)
        return self._call(url_tail, **params)

    def create(self, object_type, obj=None, **params):
        """
        Remember to put your object into a single-item dictionary with key "obj"
        """
        if not params.get("obj"):
            if obj:
                params.update({"obj" : obj})
            else:
                params = {"obj" : copy.deepcopy(params)}
                
        return self._crud("Create", object_type, **params)

    def read(self, object_type, object_id):
        return self._crud("Read", object_type, id=object_id)

    def update(self, object_type, object_id=None, obj=None, **params):
        """
        While the object_id param will ultimately get mixed in with the other
         params, it's more parallel with other crud function signatures to have
         it as a separate arg rather than in kwargs...design choice.
        
        Remember to put your object into a single-item dictionary with key "obj"
        """
        if not params.get("obj"):
            if obj:
                params = {"obj" : obj}
            else:
                params = {"obj" : params.copy()}

        object_id = params["obj"].get("id")
        if not object_id:
            msg = "{}; params:{}".format(
                "Need existing object id in order to update!",
                json.dumps(params))
            raise Exception(msg)
        
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
         Hopefully there aren't downsides to the collision I'm not aware of.
        """
        return self._call("List/{}".format(
            object_type), start=start, max=max, filters=filters, sort=sort,
                          suppress_errors=suppress_errors)

    def current_time(self):
        """
        Sometimes it's useful to know what time the API thinks it currently is.
        """
        return self._call("CurrentTime")["currentTime"]

    def invite_vendor(self, vendor_id, vendor_email):
        """
        https://developer.bill.com/hc/en-us/articles/211428083-SendVendorInvite
        
        See also CancelInvite endpoint:
         https://developer.bill.com/hc/en-us/articles/218380103
        """
        params = {
            "vendorId" : vendor_id,
            "email"    : vendor_email
        }

        return self._call('SendVendorInvite', **params)

    def attach_file(self, attachment_path, target_id=None, is_public=False):
        """
        If no target_id, document gets added to the Bill.com "Inbox".
        """
        data = {
            "fileName" : os.path.split(attachment_path)[1],
            "document" : b64encode(open(
                attachment_path, "rb").read()).decode("utf-8"),
            "isPublic" : is_public,
        }
        
        if target_id:
            data["id"] = target_id

        return self._call("UploadAttachment", **data)

    def clear_approvers(self, object_type, object_id):
        """
        https://developer.bill.com/hc/en-us/articles/210138453-ClearApprovers
        """
        return self._call(
            "ClearApprovers", entity=object_type, objectId=object_id)

    def list_user_approvals(self, user_id, object_type, approval_type,
                            marker, max=999, nested=False):
        """
        https://developer.bill.com/hc/en-us/articles/214115986-ListUserApprovals

        To Do: Implement sort, filters, and related...
        """
        return self._call("ListUserApprovals",
                          usersId=user_id, entity=object_type,
                          approvalType=approval_type, marker=marker,
                          max=max, nested=nested)
    
    def set_approvers(self, object_type, object_id, user_ids):
        """
        https://developer.bill.com/hc/en-us/articles/210138853-SetApprovers

        user_ids should be a list; the first two params should be strings
        """
        return self._call("SetApprovers",
                          entity=object_type, objectId=object_id,
                          approvers=user_ids)
    
    def record_ap_payment(self, obj=None, **params):
        """
        https://developer.bill.com/hc/en-us/articles/215407343-RecordAPPayment
        """
        if obj:
            if len(params) > 0:
                raise Exception("Don't provide both obj and params!")
            params = obj.copy()
            
        return self._call("RecordAPPayment", **params)

    def record_ar_payment(self, obj=None, **params):
        """
        https://developer.bill.com/hc/en-us/articles/213911106-RecordARPayment
        """
        if obj:
            if len(params) > 0:
                raise Exception("Don't provide both obj and params!")
            params = obj.copy()
            
        return self._call("RecordARPayment", **params)

    def set_customer_authorization(self, customer_id):
        """
        WARNING -- THIS ENABLES YOU TO ACTUALLY MOVE MONEY...REALLY BE 
         AUTHORIZED BEFORE MAKING THIS CALL!
        """
        return self._call("SetCustomerAuthorization",
                          customerId=customer_id,
                          hasAuthorizedToCharge=True)
    
    def charge_customer(self, obj=None, **params):
        """
        WARNING -- THIS ACTUALLY MOVES MONEY

        https://developer.bill.com/hc/en-us/articles/215407243-ChargeCustomer
        """
        if obj:
            if len(params) > 0:
                raise Exception("Don't provide both obj and params!")
            params = obj.copy()
            
        return self._call("ChargeCustomer", **params)

    def send_invoice(self, obj=None, **params):
        """
        WARNING -- THIS SENDS EMAILS TO BILL.COM CUSTOMERS!!!

        https://developer.bill.com/hc/en-us/articles/208197236-SendInvoice
        """
        if obj:
            if len(params) > 0:
                raise Exception("Don't provide both obj and params!")
            params = obj.copy()
            
        return self._call("SendInvoice", **params)

    def get_entity_metadata(self, object_types):
        """
        https://developer.bill.com/hc/en-us/articles/210138323-GetEntityMetadata
        """
        return self._call("GetEntityMetadata", entity=object_types) 

    def get_disbursement_data(self, sent_pay_id):
        """
        https://developer.bill.com/hc/en-us/articles/
         210138753-GetDisbursementData
        """
        return self._call("GetDisbursementData", sentPayId=sent_pay_id)

    def list_payments(self, disbursement_status, start=0, max=999):
        """
        https://developer.bill.com/hc/en-us/articles/115000149163-ListPayments
        """
        return self._call(
            "ListPayments",
            disbursementStatus=disbursement_status, start=start, max=max)
