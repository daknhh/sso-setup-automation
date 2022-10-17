import json
from bs4 import BeautifulSoup
from . import BaseClient
import os
region = os.getenv('AWS_DEFAULT_REGION')

print(f"🌎 Get region from env: AWS_DEFAULT_REGION - Region {region}")

class Client(BaseClient):
    """
    A low-level client representing Biling:

    .. code-block:: python

        import coto

        session = coto.Session()
        client = session.client('sso')

    These are the available methods:
    """
    def __init__(self, session):
        super().__init__(session)
        print(f"⚙️  Init SSO Client")
        self.__xsrf_token = None

    def _url(self, api):
        return "https://"+ region+"console.aws.amazon.com/singlesignon/{0}".format(api)

    def _xsrf_token(self):
        if self.__xsrf_token is None:
            self._get_xsrf_token()
        return self.__xsrf_token 

    def _get_xsrf_token(self):
        r = self.session()._get(
            "https://"+ region+".console.aws.amazon.com/singlesignon/identity/home?region="+region+"&state=hashArgs%23")

        if r.status_code != 200:
            raise Exception("failed get token")

        soup = BeautifulSoup(r.text, 'html.parser')
        for m in soup.find_all('meta'):
            if 'name' in m.attrs and m['name'] == "awsc-csrf-token":
                self.__xsrf_token = m['content']
                print("🔑 Successfully obtain xsrf_token")
                return

        raise Exception('unable to obtain SSO xsrf_token')



    def _post(self,operation,contentstring,path):
        x_amz_target = "com.amazon.switchboard.service.SWBService."+operation
        headers={'x-csrf-token': self._xsrf_token(),
            "X-Amz-Target": x_amz_target,
            "Content-Encoding": "amz-1.0",
            "Accept": "application/json, text/javascript, */*",
            "Content-Type": "application/json"}
        if operation == "getSyncProfile":
            apiendpoint = "https://" + region +".console.aws.amazon.com/singlesignon/api/identity-sync"
            json_body = {
                "headers": {"X-Amz-User-Agent": "aws-sdk-js/2.1048.0 promise"},
                "operation":operation,"params": {},"path":path,"region":region, "method": "GET"
            }
        if operation == "createSyncProfile" or operation == "createSyncTarget" or operation == "startSync":
            apiendpoint = "https://" + region +".console.aws.amazon.com/singlesignon/api/identity-sync"
            json_body = {
                "headers": headers,
                "operation":operation,"region":region,"path":path,"params": {},"contentString": f"{json.dumps(contentstring)}"
            }
        if operation == "createSyncFilter":
            headers={'x-csrf-token': self._xsrf_token(),
            "Content-Type": "application/json"
            }
            apiendpoint = "https://" + region +".console.aws.amazon.com/singlesignon/api/identity-sync"
            json_body = {
                "headers": headers,
                "operation":operation,"region":region,"path":path,"params": {"Augmentation": "true", "DryRun": "false"},"contentString": f"{json.dumps(contentstring)}", "method": "POST"
            }
        if operation == "deleteSyncFilter":
            headers={'x-csrf-token': self._xsrf_token(),
            "Content-Type": "application/json"
            }
            apiendpoint = "https://" + region +".console.aws.amazon.com/singlesignon/api/identity-sync"
            json_body = {
                "headers": headers,
                "operation":operation,"region":region,"path":path,"params": {}, "method": "DELETE"
            }
        if operation == "listSyncFilters":
            apiendpoint = "https://" + region +".console.aws.amazon.com/singlesignon/api/identity-sync"
            json_body = {
                "headers": headers,
                "operation":operation,"region":region,"path":path,"params": contentstring, "method": "GET"
            }

        r = self.session()._post(
            apiendpoint,
            data=json.dumps(json_body),
            headers=headers
            )
        if r.status_code == 200:
            print(f"✅ Successfully invoked: {operation}")
        if r.status_code != 200:
            raise Exception(f"🚨 Failed to invoke: {operation} - Method: Post - Error: {r.text} - {r.status_code}")

        return r

    def _delete(self,operation,contentstring,path):
        x_amz_target = "com.amazon.switchboard.service.SWBService."+operation
        headers={'x-csrf-token': self._xsrf_token(),
            "X-Amz-Target": x_amz_target,
            "Content-Encoding": "amz-1.0",
            "Accept": "application/json, text/javascript, */*",
            "Content-Type": "application/json"}
        if operation == "deleteSyncProfile":
            apiendpoint = "https://" + region +".console.aws.amazon.com/singlesignon/api/identity-sync"
            json_body = {
                "headers": headers,
                "operation":operation,"region":region,"path":path,"params": "{}"
            }
        else:
            apiendpoint = "https://" + region +".console.aws.amazon.com/singlesignon/api/peregrine"
            json_body = {
                "headers": headers,
                "operation":operation,"contentString": f"{json.dumps(contentstring)}",
                "region":region,"path":path
            }
        r = self.session()._delete(
            apiendpoint,
            data=json.dumps(json_body),
            headers={'x-csrf-token': self._xsrf_token(),
            "X-Amz-Target": x_amz_target,
            "Accept": "application/json, text/javascript, */*","content-type":"application/json"}
            )
        if r.status_code == 200:
            print(f"✅ Successfully invoked: {operation} - Method: Delete")
        if r.status_code != 200:
            raise Exception(f"🚨 Failed to invoke: {operation} - Method: Delete")

        return r

    # sso api

    def create_sync_filter(self,profilename, filtertype, associateddomain,samaccountname):
        """
        Obtain the list of the sso associations.

        Status:

        Request Syntax:
            .. code-block:: python

                response = client.create_sync_filter(
                    profilename,
                    FilterType,
                    associateddomain,
                    samaccountname
                )

        Returns:
            string: status
        """
        operation = "createSyncFilter"
        path = "/v0/profiles/"+ profilename + "/filters"
        contentstring = {"FilterType":filtertype,"Attributes":"{\"associateddomain\":[\"" + associateddomain+ "\"],\"samaccountname\":[\""+samaccountname+"\"]}","Effect":"INCLUDE"}
        r = self._post(operation,contentstring,path)
        return json.loads(r.text)

    def delete_sync_filter(self,profilename, syncfilterid):
        """
        Delete Sync Filter of AWS SSO.

        Status:

        Request Syntax:
            .. code-block:: python

                response = client.deleteSyncFilter(
                    profilename,
                    syncfilterid
                )

        Returns:
            string: status
        """
        operation = "deleteSyncFilter"
        path = "/v0/profiles/"+ profilename + "/filters/" + syncfilterid
        contentstring = {}
        r = self._post(operation,contentstring,path)
        return json.loads(r.text)

    def list_sync_filters(self,profilename, filtertype):
        """
        List Sync Filter of AWS SSO.

        Status:

        Request Syntax:
            .. code-block:: python

                response = client.listSyncFilters(
                    profilename
                    filtertypes
                )

        Returns:
            string: status
        """
        operation = "listSyncFilters"
        path = "/v0/profiles/"+ profilename + "/filters"
        contentstring = { "Augmentation": "true", "FilterType": filtertype,"MaxResults": "100"}
        r = self._post(operation,contentstring,path)
        return json.loads(r.text)

    def list_associations(self):
        """
        Obtain the list of the sso associations.

        Status:

        Request Syntax:
            .. code-block:: python

                response = client.list_associations()

        Returns:
            string: status
        """
        operation = "ListDirectoryAssociations"
        path = "/control/"
        contentstring = {}
        r = self._post(operation,contentstring,path)
        return json.loads(r.text)

    def disassociate_directory(self,directoryId,directoryType):
        """
        Associate Directory to the sso.

        Status:

        Request Syntax:
            .. code-block:: python

                response = client.disassociate_directory(
                    directoryId, #Id of the directory
                    directoryType #eg. ADConnector
                )

        Returns:
            string: status
        """
        operation = "DisassociateDirectory"
        path = "/control/"
        contentstring = {"directoryId":directoryId,"directoryType":directoryType}
        r = self._post(operation,contentstring,path)
        return json.loads(r.text)

    def create_synctarget(self,profilename, SyncTargetName,TargetResourceArn):
        """
        Create Sync Target for sso.

        Status:

        Request Syntax:
            .. code-block:: python

                response = client.create_synctarget(
                    profilename, #eg . SynchronizationToActiveDirectoryAwsSso
                    SyncTargetName, # eg. IdentityStoreForSSO
                    TargetResourceArn #eg identitystore/directoryid                )

        Returns:
            string: status
        """
        operation = "createSyncTarget"
        path = "/v0/profiles/"+ profilename + "/targets"
        contentstring = {"SyncTargetName":SyncTargetName,"TargetResourceArn":TargetResourceArn}
        r = self._post(operation,contentstring,path)
        return json.loads(r.text)

    def start_sync(self,profilename):
        """
        Start Sync for sso.

        Status:

        Request Syntax:
            .. code-block:: python

                response = client.start_sync(
                    profilename, #eg . SynchronizationToActiveDirectoryAwsSso
        )

        Returns:
            string: status
        """
        operation = "startSync"
        path = "/v0/profiles/"+ profilename + "/startSync"
        contentstring = ""
        r = self._post(operation,contentstring,path)
        return "␖ Started Sync"

    def get_ssoconfiguration(self):
        """
        Get the Configuration of the SSO.

        Status:

        Request Syntax:
            .. code-block:: python

                response = client.get_ssoconfiguration()

        Returns:
            string: status
        """
        operation = "GetSsoConfiguration"
        path = "/control/"
        contentstring = {}
        r = self._post(operation,contentstring,path)
        return json.loads(r.text)

    def get_mfadevicemanagementfordirectory(self,directoryId,directoryType):
        """
        Get Mfa Device Management For Directory.

        Status:

        Request Syntax:
            .. code-block:: python

                response = client.get_mfadevicemanagementfordirectory(
                    directoryId, #Id of the directory
                    directoryType #eg. ADConnector
                )

        Returns:
            string: status
        """
        operation = "GetMfaDeviceManagementForDirectory"
        path = "/control/"
        contentstring = {"directoryId":directoryId,"directoryType":directoryType}
        r = self._post(operation,contentstring,path)
        return json.loads(r.text)

    def get_syncprofile(self,profilename):
        """
        Get get Sync Profile.

        Status:

        Request Syntax:
            .. code-block:: python

                response = client.get_syncprofile(
                    profilename eg. SynchronizationToActiveDirectoryAwsSso
                )

        Returns:
            string: status
        """
        operation = "getSyncProfile"
        path = "/v0/profiles/" + profilename
        contentstring = {}
        r = self._post(operation,contentstring,path)
        return json.loads(r.text)

    def delete_syncprofile(self,profilename):
        """
        Get Mfa Device Management For Directory.

        Status:

        Request Syntax:
            .. code-block:: python

                response = client.delete_syncprofile(
                    profilename eg. SynchronizationToActiveDirectoryAwsSso
                )

        Returns:
            string: status
        """
        operation = "deleteSyncProfile"
        path = "/v0/profiles/" + profilename
        params = {}
        r = self._delete(operation,params,path)
        return json.loads(r.text)

    def create_syncprofile(self,SyncProfileName,SourceResourceArn):
        """
        Create Sync Profile.

        Status:

        Request Syntax:
            .. code-block:: python

                response = client.associate_directory(
                    SyncProfileName, #Id of the directory
                    SourceResourceArn #eg. Arn of the Source
                )

        Returns:
            string: status
        """
        operation ="createSyncProfile"
        path = "/v0/profiles"
        contentstring = {"SyncProfileName":SyncProfileName,"SourceResourceArn":SourceResourceArn}
        r = self._post(operation,contentstring,path)
        return json.loads(r.text)



    def associate_directory(self,directoryId,directoryType):
        """
        Associate Directory to the sso.

        Status:

        Request Syntax:
            .. code-block:: python

                response = client.associate_directory(
                    directoryId, #Id of the directory
                    directoryType #eg. ADConnector
                )

        Returns:
            string: status
        """
        operation = "AssociateDirectory"
        path = "/control/"
        contentstring = {"directoryId":directoryId,"directoryType":directoryType}
        r = self._post(operation,contentstring,path)
        return json.loads(r.text)
