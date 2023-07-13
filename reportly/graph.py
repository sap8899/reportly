# graph.py>

import datetime
import json
from configparser import SectionProxy
from azure.identity import DeviceCodeCredential, ClientSecretCredential
from msgraph.core import GraphClient
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
from gui import Gui
from ips import IPS
import requests

class Graph:
    settings: SectionProxy
    device_code_credential: DeviceCodeCredential
    user_client: GraphClient
    client_credential: ClientSecretCredential
    app_client: GraphClient

    def __init__(self, config: SectionProxy, sus_user, start_date, end_date, out_file="report.html"):
        self.settings = config
        client_id = self.settings['clientId']
        tenant_id = self.settings['tenantId']
        graph_scopes = self.settings['graphUserScopes'].split(' ')
        self.out_file = out_file
        self.sus_user = sus_user
        self.start_date = start_date
        self.end_date = end_date
        self.audit_initiated = []
        self.audit_target = []
        self.audit_signin = []
        self.bad_signin = []
        self.owned_objects = []
        self.owned_devices = []
        self.ips = {}
        self.roles_list = {}
        self.accept_activity = ["Remove owner from group", "Remove member from group", "Add owner to group", "Add member to role", "Add member to group"]
        self.not_accept_category = ["GroupManagement"]
        self.device_code_credential = DeviceCodeCredential(client_id,tenant_id = tenant_id)
        self.device_code_credential = DeviceCodeCredential(client_id, tenant_id = tenant_id)
        self.user_client = GraphClient(credential=self.device_code_credential, scopes=graph_scopes)

    def is_group_admin(self, groupId):
        endpoint = f'https://graph.microsoft.com/v1.0/groups/{groupId}/memberOf'
        request_url = endpoint
        user_response = self.user_client.get(request_url)
        json_response = user_response.json()
        if not 'value' in json_response or len(json_response['value']) == 0:
            return ""
        results = json_response['value']
        group_roles = ""
        for result in results:
            if result['@odata.type'] == '#microsoft.graph.directoryRole':
                displayName = result['displayName']
                group_roles += displayName + " ;"
        return group_roles



    def parse_owned_objects(self, objects):
        for object in objects:
            temp_dict = {}
            oKeys = object.keys()
            oType = object['@odata.type'].split(".")[-1] if '@odata.type' in oKeys else "None."
            oId = object['id'] if 'id' in oKeys else "None."
            oDisplayName = object['displayName'] if 'displayName' in oKeys else "None."
            temp_dict["type"] = oType
            temp_dict["id"] = oId
            temp_dict["displayName"] = oDisplayName
            group_roles = self.is_group_admin(oId) if oType == 'group' else ""
            temp_dict["groupRoles"] = group_roles
            self.owned_objects.append(temp_dict)

    def get_owned_objects(self, url='url', pagination=False):
        endpoint = f'https://graph.microsoft.com/beta/users/{self.sus_user}/ownedObjects'
        request_url = f'{endpoint}'
        if pagination:
            request_url = url
        user_response = self.user_client.get(request_url)
        json_response = user_response.json()
        if not 'value' in json_response or len(json_response['value']) == 0:
            return "This user does not own any objects."
        if '@odata.nextLink' in user_response:
            self.parse_owned_objects(json_response['value'])
            pagination_url = json_response['@odata.nextLink']
            self.get_owned_objects(self, pagination_url, pagination=True)
        self.parse_owned_objects(json_response['value'])
        if len(self.audit_target) == 0:
            return "This user does not own any objects."
        return user_response.json()
    
    def parse_owned_devices(self, objects):
        for object in objects:
            temp_dict = {}
            oKeys = object.keys()
            oId = object['id'] if 'id' in oKeys else "None."
            dId = object['deviceId'] if 'deviceId' in oKeys else "None."
            dDisplayName = object['displayName'] if 'displayName' in oKeys else "None."
            isCompliant = object['isCompliant'] if 'isCompliant' in oKeys else "None."
            temp_dict["deviceID"] = dId
            temp_dict["objectID"] = oId
            temp_dict["displayName"] = dDisplayName
            temp_dict["isCompliant"] = isCompliant
            self.owned_devices.append(temp_dict)

    def get_owned_devices(self, url='url', pagination=False):
        endpoint = f'https://graph.microsoft.com/beta/users/{self.sus_user}/ownedDevices'
        request_url = f'{endpoint}'
        if pagination:
            request_url = url
        user_response = self.user_client.get(request_url)
        json_response = user_response.json()
        if not 'value' in json_response or len(json_response['value']) == 0:
            return "This user does not own any devices."
        if '@odata.nextLink' in user_response:
            self.parse_owned_devices(json_response['value'])
            pagination_url = json_response['@odata.nextLink']
            self.get_owned_devices(self, pagination_url, pagination=True)
        self.parse_owned_devices(json_response['value'])
        if len(self.audit_target) == 0:
            return "This user does not own any devices."
        return user_response.json()


    def bad_sigin_errors(self):
        signin = self.bad_signin
        error_code_list = [50088, 50131,500021,500022,50053,50135,53011,530034,53010,530032]
        out = []
        for event in signin:
            if event["code"] in error_code_list:
                out.append(event)
        
        return out
                
    def get_ips(self):
        return self.ips

    def get_user_token(self):
        graph_scopes = self.settings['graphUserScopes']
        access_token = self.device_code_credential.get_token(graph_scopes)
        return access_token.token

    def get_user(self):
        endpoint = '/me'
        # Only request specific properties
        select = 'displayName,mail,userPrincipalName'
        request_url = f'{endpoint}?$select={select}'

        user_response = self.user_client.get(request_url)
        return user_response.json()

    def get_sus_user(self):
        endpoint = f'/users/{self.sus_user}'
        # Only request specific properties
        select = 'id,userPrincipalName,displayName,onPremisesDistinguishedName,onPremisesSyncEnabled,onPremisesUserPrincipalName,onPremisesSecurityIdentifier,createdDateTime,userType,lastPasswordChangeDateTime'
        request_url = f'{endpoint}?$select={select}'

        user_response = self.user_client.get(request_url)
        return user_response.json()

    def get_mfa_info(self):
        user = self.get_sus_user()
        principalName = user['userPrincipalName']
        endpoint = 'https://graph.microsoft.com/beta/reports/credentialUserRegistrationDetails'
        mfa_filter = f"userPrincipalName eq '{principalName}'"
        request_url = f'{endpoint}?$filter={mfa_filter}'
        user_response = self.user_client.get(request_url)
        json_response = user_response.json()
        if not 'value' in json_response or len(json_response['value']) == 0:
            return "This user does not have any MFA configured."
        mfa = json_response['value']
        data = mfa[0]
        authMetods = data["authMethods"]        
        return authMetods
    def get_location(self,ip):
        response = requests.get(f'https://ipapi.co/{ip}/json/').json()
        location_data = {
            "city": response.get("city"),
            "region": response.get("region"),
            "country": response.get("country_name")
        }
        return location_data
    
    def get_ips_loc(self,ips_dict):
        for ip in ips_dict.keys():
            ip_loc = self.get_location(ip)
            ips_dict[ip]['City'] = ip_loc['city']
            ips_dict[ip]['region'] = ip_loc['region']
            ips_dict[ip]['country'] = ip_loc['country']
        return ips_dict

    def get_sus_roles(self):
        roles = []
        user = self.get_sus_user()
        id = user['id']
        endpoint = '/roleManagement/directory/roleAssignments'
        role_filter = f"principalId eq '{id}'"
        request_url = f'{endpoint}?$filter={role_filter}'
        user_response = self.user_client.get(request_url)
        json_response = user_response.json()
        if not 'value' in json_response or len(json_response['value']) == 0:
            return "This user has no roles."
        with open(r"roles_map.json") as json_file:
            json_data = json.load(json_file)
        for role in json_response['value']:
            role_id = role['roleDefinitionId']
            roles.append(json_data[role_id])
        return roles
    
    def get_eligible_roles(self):
        eligible_roles = []
        user = self.get_sus_user()
        id = user['id']
        endpoint_eligible = '/roleManagement/directory/roleEligibilityScheduleInstances'
        role_filter = f"principalId eq '{id}'"
        request_url_eligible = f'{endpoint_eligible}?$filter={role_filter}'
        user_response = self.user_client.get(request_url_eligible)
        json_response = user_response.json()
        if not 'value' in json_response or len(json_response['value']) == 0:
            return "This user is not eligible to any role."
        with open(r"roles_map.json") as json_file:
            json_data = json.load(json_file)
        for role in json_response['value']:
            role_id = role['roleDefinitionId']
            eligible_roles.append(json_data[role_id])
        return eligible_roles          

    def get_sus_groups(self):
        endpoint = f'/users/{self.sus_user}/memberOf/microsoft.graph.group'
        select = 'id,displayName,description'
        request_url = f'{endpoint}?$select={select}'
        user_response = self.user_client.get(request_url)
        json_response = user_response.json()
        if not 'value' in json_response or len(json_response['value']) == 0:
            return {}
        group_dict = self.parse_sus_groups(json_response['value'], transitive="False")
        return group_dict
    
    def parse_sus_groups(self, groups, transitive):
        groups_dict = {}
        name_list = []
        description_list = []
        id_list = []
        roles_list = []
        transitive_list = []
        for group in groups:
            name_list.append(group['displayName'])
            description_list.append(group['description'])
            id_list.append(group['id'])
            roles_list.append(self.is_group_admin(group['id']))
            transitive_list.append(transitive)
        groups_dict['GroupName'] = name_list
        groups_dict['Description'] = description_list
        groups_dict['Id'] = id_list
        groups_dict['GroupRoles'] = roles_list
        groups_dict['Transitive'] = transitive_list
        return groups_dict

    def get_sus_groups_transitive(self):
        endpoint = f'/users/{self.sus_user}/transitiveMemberOf/microsoft.graph.group'
        select = 'id,displayName,description'
        request_url = f'{endpoint}?$select={select}'
        user_response = self.user_client.get(request_url)
        json_response = user_response.json()
        if not 'value' in json_response or len(json_response['value']) == 0:
            return {}
        group_dict = self.parse_sus_groups(json_response['value'], transitive="True")
        return group_dict


    def get_audit_target(self, url='/auditLogs/directoryAudits', pagination=False):
        sus = self.sus_user
        endpoint = '/auditLogs/directoryAudits'
        filter = f"targetResources/any(t:t/userPrincipalName eq  '{sus}')"
        request_url = f"{endpoint}?$filter={filter}"
        if pagination:
            request_url = url

        user_response = self.user_client.get(request_url)
        json_response = user_response.json()
        if not 'value' in json_response or len(json_response['value']) == 0:
            return "No operations have been performed on this user."
        if '@odata.nextLink' in user_response:
            self.parse_audit(json_response['value'], "target")
            pagination_url = json_response['@odata.nextLink']
            self.get_audit_target(self, pagination_url, pagination=True)
        self.parse_audit(json_response['value'], "target")
        if len(self.audit_target) == 0:
            return "No operations have been performed on this user."


    def get_audit_initiated(self, url='/auditLogs/directoryAudits', pagination=False):
        sus = self.sus_user
        endpoint = '/auditLogs/directoryAudits'
        filter = f"initiatedBy/user/userPrincipalName eq '{sus}'"
        request_url = f"{endpoint}?$filter={filter}"
        if pagination:
            request_url = url
        
        user_response = self.user_client.get(request_url)
        json_response = user_response.json()
        if not 'value' in json_response or len(json_response['value']) == 0:
            return "This user has not performed any action."
        if '@odata.nextLink' in user_response:
            self.parse_audit(json_response['value'], "initiated")
            pagination_url = json_response['@odata.nextLink']
            self.get_audit_initiated(self, pagination_url, pagination=True)
        self.parse_audit(json_response['value'], "initiated")
        if len(self.audit_initiated) == 0:
            return "This user has not performed any action."

    def parse_audit(self, audit, func):
        start = datetime.datetime.strptime(self.start_date, '%Y-%m-%d').date()
        end = datetime.datetime.strptime(self.end_date, '%Y-%m-%d').date()
        for event in audit:
            temp_dict = {}
            targets_output = "<br>Targets:<br>"
            string_initiate = ""
            category = event['category']
            activity = event['activityDisplayName']
            created = event['activityDateTime']
            id = event['id']
            result = event['result']
            if category not in self.not_accept_category or activity in self.accept_activity:
                targets = event['targetResources']
                for target in targets:
                
                    target_id = target['id']
                    target_displayName = target['displayName']
                    target_type = target['type']
                    
                    tagret_string = f"Type: {target_type}, Id: {target_id}, DisplayName: {target_displayName} "
                    if target_type == "User":
                        target_upn = target['userPrincipalName']
                        tagret_string += f", UPN: {target_upn} "
                    targets_output += tagret_string
                    targets_output += """;<br>"""

                initiate_user = event['initiatedBy']['user']
                initiate_app = event['initiatedBy']['app']
                if initiate_user:
                    user_name = initiate_user['userPrincipalName']
                    string_initiate += f"User: userPrincipalName: {user_name} ; "
                if initiate_app:
                    app_name = initiate_app['displayName']
                    service_id = initiate_app['servicePrincipalId']
                    string_initiate += f"App: displayName: {app_name}, servicePrincipalId: {service_id} ;"
            else:
                targets_output = "Not relevant"
            created_temp = created.split(".")[0]
            created_time = datetime.datetime.strptime(created_temp, '%Y-%m-%dT%H:%M:%S').date()
            
            if created_time > start and created_time < end:
                temp_dict["id"] = id
                temp_dict["category"] = category
                temp_dict["activity"] = activity
                temp_dict["created"] = created
                temp_dict["result"] = result
                if(func == "initiated"):
                    temp_dict["Information"] = targets_output
                    self.audit_initiated.append(temp_dict)
                if(func == "target"):
                    targets_output += "InitiatedBy:<br>" + string_initiate
                    temp_dict["Information"] = targets_output
                    self.audit_target.append(temp_dict)
    
    def create_graph_initiated(self):
        source = pd.DataFrame(self.audit_initiated)
        fig = px.scatter(source, x=source['created'], y=source['activity'],color="result", title=f"Initiated Activities by {self.sus_user}",
             hover_data=[source['Information']],
             labels={
                     "created": "Time",
                     "activity": "Activity",
                 })
        fig.update_layout(
            hoverlabel=dict(
                bgcolor="white",
                font_size=14,
            )
        )
        fig.update_layout(paper_bgcolor=" #e6f0ff")
        url = fig.write_html("report_initiated.html")


    def create_graph_target(self):
        source = pd.DataFrame(self.audit_target)
        fig = px.scatter(source, x=source['created'], y=source['activity'],color="result", title=f"Activities performed on {self.sus_user}", 
            hover_data=[source['Information']],
            labels={
                     "created": "Time",
                     "activity": "Activity",
                 })
        fig.update_layout(
            hoverlabel=dict(
                bgcolor="white",
                font_size=14,
            )
        )
        fig.update_layout(paper_bgcolor="  #e6f0ff")
        url = fig.write_html("report_target.html")


    def get_audit_signIn_success(self):
        sus = self.sus_user.lower()
        endpoint = '/auditLogs/signIns'
        filter = f"userPrincipalName eq '{sus}' and status/errorCode eq 0"
        request_url = f"{endpoint}?$filter={filter}"

        user_response = self.user_client.get(request_url)
        json_response = user_response.json()
        if not 'value' in json_response or len(json_response['value']) == 0:
            return "No logs"
        self.parse_signin(json_response['value'], "success")
        if len(self.audit_signin) == 0:
            return "No logs"
        
        

    def get_audit_signIn_failed(self):
        sus = self.sus_user.lower()
        endpoint = '/auditLogs/signIns'
        filter = f"userPrincipalName eq '{sus}' and status/errorCode ne 0"
        request_url = f"{endpoint}?$filter={filter}"

        user_response = self.user_client.get(request_url)
        json_response = user_response.json()
        if not 'value' in json_response or len(json_response['value']) == 0:
            return "No logs"
        self.parse_signin(json_response['value'], "failed")
        if len(self.audit_signin) == 0:
            return "No logs"
    

    def parse_signin(self, audit, func):
        start = datetime.datetime.strptime(self.start_date, '%Y-%m-%d').date()
        end = datetime.datetime.strptime(self.end_date, '%Y-%m-%d').date()
        for event in audit:
            temp_dict = {}
            created = event['createdDateTime']
            resource = event['resourceDisplayName']
            interactive = event['isInteractive']
            ip = event['ipAddress']
            app_used = event['clientAppUsed']

            hover_string = f"<br>Interactive: {interactive}<br>ip: {ip}<br>app used: {app_used}"
            if func == "failed":
                status_dict = event['status']
                code = status_dict['errorCode']
                reason = status_dict['failureReason']
                details = status_dict['additionalDetails']
                hover_string+= f"<br>code: {code} ; reason: {reason} ; details: {details}"
            created_temp = created.split("Z")[0]
            created_time = datetime.datetime.strptime(created_temp, '%Y-%m-%dT%H:%M:%S').date()
            
            if created_time > start and created_time < end:
                temp_dict["type"] = func
                temp_dict["created"] = created
                temp_dict["resource"] = resource
                temp_dict["Information"] = hover_string
                self.audit_signin.append(temp_dict)
                if self.ips.get(ip) != None:
                    ip_object = self.ips[ip]
                    ip_object["count"] += 1
                    ip_object["app_used"].add(app_used)
                    ip_object["resource"].add(resource)
                else:
                    self.ips[ip] = {"count":1, "app_used":set([app_used]), "resource":set([resource])}
                if func == "failed":
                    bad_dict = {"created":created,"resource":resource,"ip":ip,"app_used":app_used,"code":code,"reason":reason,"details":details}
                    self.bad_signin.append(bad_dict)



    def create_graph_signin(self):
        signin = pd.DataFrame(self.audit_signin)
        fig = px.scatter(signin, x=signin['created'], y=signin['resource'], color="type",
                 title="Sign-in graph", hover_data=[signin['Information']],
                 labels={
                     "created": "Time",
                     "resource": "Resource",
                     "type": "Login status"
                 }
                )
        fig.update_layout(paper_bgcolor=" #e6f0ff")
        url = fig.write_html("report_signin.html")

    def generate_report(self, initiated, target, signin,ips, signin_errors):
        ips = self.get_ips_loc(ips)
        self.get_owned_objects()
        owned_objects = self.owned_objects if self.owned_objects else "This user does not own any objects."
        self.get_owned_devices()
        owned_devices = self.owned_devices if self.owned_devices else "This user does not own any devices."
        groups_transitive = self.get_sus_groups_transitive()
        groups_non_transitive = self.get_sus_groups()
        groups_dict = {}
        groups_dict["transitive"] = groups_transitive
        groups_dict["nonTransitive"] = groups_non_transitive
        user = self.get_sus_user()
        roles = self.get_sus_roles()
        eligible_roles = self.get_eligible_roles()
        roles_dict = {}
        roles_dict["Roles"] = roles
        roles_dict["Eligible"] = eligible_roles
        mfa = self.get_mfa_info()
        gui: Gui = Gui(user, groups_dict, roles_dict, initiated, target, signin, ips, signin_errors, mfa, owned_objects, owned_devices)
        gui.generate_report(self.out_file)
