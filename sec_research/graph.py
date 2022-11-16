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

class Graph:
    settings: SectionProxy
    device_code_credential: DeviceCodeCredential
    user_client: GraphClient
    client_credential: ClientSecretCredential
    app_client: GraphClient

    def __init__(self, config: SectionProxy, sus_user, start_date, end_date):
        self.settings = config
        client_id = self.settings['clientId']
        tenant_id = self.settings['tenantId']
        graph_scopes = self.settings['graphUserScopes'].split(' ')
        self.sus_user = sus_user
        self.start_date = start_date
        self.end_date = end_date
        self.audit_initiated = []
        self.audit_target = []
        self.audit_signin = []
        self.roles_list = {}
        self.accept_activity = ["Remove owner from group", "Remove member from group", "Add owner to group", "Add member to role", "Add member to group"]
        self.accept_category = ["UserManagement", "ApplicationManagement", "RoleManagement"]
        self.device_code_credential = DeviceCodeCredential(client_id, tenant_id = tenant_id)
        self.user_client = GraphClient(credential=self.device_code_credential, scopes=graph_scopes)

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
        select = 'id,userPrincipalName,displayName,onPremisesDistinguishedName,onPremisesSyncEnabled,onPremisesUserPrincipalName,onPremisesSecurityIdentifier,createdDateTime'
        request_url = f'{endpoint}?$select={select}'

        user_response = self.user_client.get(request_url)
        return user_response.json()

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

    def get_sus_groups(self):
        endpoint = f'/users/{self.sus_user}/memberOf'
        select = 'id,displayName,description'
        request_url = f'{endpoint}?$select={select}'
        user_response = self.user_client.get(request_url)
        json_response = user_response.json()
        if not 'value' in json_response or len(json_response['value']) == 0:
            return "This user is not a member of any group."
        group_dict = self.parse_sus_groups(json_response['value'])
        return group_dict
    
    def parse_sus_groups(self, groups):
        groups_dict = {}
        name_list = []
        description_list = []
        id_list = []
        for group in groups:
            name_list.append(group['displayName'])
            description_list.append(group['description'])
            id_list.append(group['id'])
        groups_dict['GroupName'] = name_list
        groups_dict['Decription'] = description_list
        groups_dict['Id'] = id_list
        return groups_dict


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
            if category in self.accept_category or activity in self.accept_activity:
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
                if(func == "initiated"):
                    temp_dict["Information"] = targets_output
                    self.audit_initiated.append(temp_dict)
                if(func == "target"):
                    targets_output += "InitiatedBy:<br>" + string_initiate
                    temp_dict["Information"] = targets_output
                    self.audit_target.append(temp_dict)
    
    def create_graph_initiated(self):
        source = pd.DataFrame(self.audit_initiated)
        fig = px.scatter(source, x=source['created'], y=source['activity'], title=f"Initiated Activities by {self.sus_user}",
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
        fig = px.scatter(source, x=source['created'], y=source['activity'], title=f"Activities performed on {self.sus_user}", 
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
        #fig.show()
        fig.update_layout(paper_bgcolor=" #e6f0ff")
        url = fig.write_html("report_signin.html")

    def generate_report(self, initiated, target, signin):
        groups = self.get_sus_groups()
        user = self.get_sus_user()
        roles = self.get_sus_roles()
        gui: Gui = Gui(user, groups, roles, initiated, target, signin)
        gui.generate_report()