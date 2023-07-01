# gui.py>

import datetime
import json
from configparser import SectionProxy
from azure.identity import DeviceCodeCredential, ClientSecretCredential
from msgraph.core import GraphClient
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go


class Gui:    
    def __init__(self, sus, groups, roles_dict, initiated, target, signin,ips,signin_erros, mfa, owned_objects, owned_devices):
        self.sus = sus
        self.groups = groups
        self.roles = roles_dict["Roles"]
        self.eligible_roles = roles_dict["Eligible"]
        self.initiated = initiated
        self.target = target
        self.signin = signin
        self.signin_erros = signin_erros
        self.ips = ips
        self.mfa = mfa
        self.owned_objects = owned_objects
        self.owned_devices = owned_devices

    def parse_owned_objects(self):
        if self.owned_objects == "This user does not own any objects.":
            return self.owned_objects
    
        objects = pd.DataFrame(data=self.owned_objects)
        objects = objects.fillna(' ')
        objects_out = objects.style.to_html(classes='table table-stripped')
        return objects_out
    

    def parse_owned_devices(self):
        if self.owned_devices == "This user does not own any devices.":
            return self.owned_devices
    
        objects = pd.DataFrame(data=self.owned_devices)
        objects = objects.fillna(' ')
        objects_out = objects.style.to_html(classes='table table-stripped')
        return objects_out
    

    def parse_mfa(self):
        if len(self.mfa)==0:
            return "This user does not have any MFA configured."
        mfa_string = ""
        for method in self.mfa:
            mfa_string += method + "<br>"
        return mfa_string

    def parse_bad_signin(self):
        if len(self.signin_erros) == 0:
            return "No suspicious events."
        errors = pd.DataFrame(data=self.signin_erros)
        errors = errors.fillna(' ')
        errors_html = errors.style.to_html(classes='table table-stripped')
        return errors_html

    def parse_ips(self):
        if len(self.ips) == 0:
            return "No IPs."
        sus_ips = pd.DataFrame(data=self.ips)
        sus_ips = sus_ips.fillna(' ')
        ips_out = sus_ips.style.to_html(classes='table table-stripped')
        return ips_out


    def create_roles_string(self):
        if self.roles == "This user has no roles.":
            return self.roles
        roles_string = ""
        for role in self.roles:
            roles_string += role + "<br>"

        return roles_string
    
    def create_eligible_roles_string(self):
        if self.eligible_roles == "This user is not eligible to any role.":
            return self.eligible_roles
        roles_string = ""
        for role in self.eligible_roles:
            roles_string += role + "<br>"

        return roles_string

    def create_groups_output(self):
        if self.groups == "This user is not a member of any group.":
            return self.groups
        groups_df = pd.DataFrame(data=self.groups)
        groups_html = groups_df.style.to_html(classes='table table-stripped')
        return groups_html

    def generate_report(self):
        errors_html = self.parse_bad_signin()
        groups_html = self.create_groups_output()
        roles_html = self.create_roles_string()
        eligible_html = self.create_eligible_roles_string()
        mfa_html = self.parse_mfa()
        owned_objects = self.parse_owned_objects()
        owned_devices = self.parse_owned_devices()
        if self.sus['onPremisesSyncEnabled']:
            sync_data = f"SID: {self.sus['onPremisesSecurityIdentifier']}, UserPrincipalName: {self.sus['onPremisesUserPrincipalName']}"
        else:
            sync_data = "User is not synced."
        
        if self.initiated == "This user has not performed any action.":
            initiated_html = self.initiated
        else:
            #with open(r"report_initiated.html", 'r') as f:
            f = open(r"report_initiated.html", encoding="utf8")
            initiated_html = f.read()
        
        if self.target == "No operations have been performed on this user.":
            target_html = self.target
        else:
            #with open(r"report_target.html", 'r') as f:
            f = open(r"report_target.html", encoding="utf8")
            target_html = f.read()
                #target_html = f.read()

        if self.signin == "This user has not logged in.":
            sigin_html = self.signin
            sus_ips = "No IPs."
        else:
            #with open(r"report_signin.html", 'r') as f:
            #    sigin_html = f.read()
            f = open(r"report_signin.html", encoding="utf8")
            sigin_html = f.read()
            sus_ips = self.parse_ips()
        
        html_string = '''
<!doctype html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>Report</title>
        <style>
            section { 
                text-align: center;
            }
            p.thick {
                font-weight: bold;
                }
            body { 
                margin:0 100; background:   #e6f0ff; font: 15px Arial, sans-serif; color: black;
                }
            .collapsible {
                background-color: #b3deff;
                color: black;
                cursor: pointer;
                padding: 18px;
                width: 100%;
                border: none;
                text-align: left;
                outline: none;
                font-size: 15px;
                }

                .active, .collapsible:hover {
                background-color:    #66a3ff;
                }

                .content {
                padding: 0 18px;
                display: none;
                overflow: hidden;
                background-color:    #b3d1ff;
                }
                .grid-container {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    grid-gap: 20px;
                } 
        </style>
    </head>
    
    <body>
        <img src="logo.png" width="200" height="100">
        <!-- *** Section 0 *** --->
        <section>
        <h3 style="text-align:center">User details</h3>
        <div class="grid-container">
        <div class="grid-child A">
        <p class="thick">Id</p> ''' + self.sus['id'] + '''<br>
        <p class="thick">DisplayName</p> ''' + self.sus['displayName'] + '''<br>
        <p class="thick">UserPrincipalName</p> ''' + self.sus['userPrincipalName'] + '''<br>
        </div>
        <div class="grid-child B">
        <p class="thick">OnPremises</p> ''' + sync_data + '''<br>
        <p class="thick">Created</p> ''' + self.sus['createdDateTime'] + '''<br>
        <p class="thick">User type</p> ''' + self.sus['userType'] + '''<br>
        <p class="thick">Last password change</p> ''' + self.sus['lastPasswordChangeDateTime'] + '''<br>
        </div>
        </div>
        
        
        <p class="thick">Groups</p><br>
        <button type="button" class="collapsible">Click to show groups</button>
<div class="content">
   ''' + groups_html + '''
</div>
<div class="grid-container">
<div class="grid-child A">
        <p class="thick">Roles</p><br>
        <button type="button" class="collapsible">Click to show roles</button>
<div class="content">
   ''' + roles_html + '''
</div>
</div>
<div class="grid-child B">
        <p class="thick">Eligible Roles</p><br>
        <button type="button" class="collapsible">Click to show roles</button>
<div class="content">
   ''' + eligible_html + '''
</div>
</div>
</div>
        <p class="thick">Owned objects</p><br>
        <button type="button" class="collapsible">Click to show owned objects</button>
<div class="content">
   ''' + owned_objects + '''
</div> 
        <p class="thick">Owned devices</p><br>
        <button type="button" class="collapsible">Click to show owned devices</button>
<div class="content">
   ''' + owned_devices + '''
</div> 
        </section>
        <!-- *** Section 1 *** --->
        <h2>Initiated Activities</h2>
        ''' + initiated_html + '''

        <!-- *** Section 2 *** --->
        <h2>Activities as target</h2>
        ''' + target_html + '''

        <!-- *** Section 2 *** --->
        <h2>User sign-in</h2>
        ''' + sigin_html + '''
        <p class="thick">IPs information</p><br>
        <button type="button" class="collapsible">Click to show ips information</button>
<div class="content">
   ''' + sus_ips + '''
</div>
        <p class="thick">Suspicios failed logins</p><br>
        <button type="button" class="collapsible">Click to show suspiscious failed logins</button>
<div class="content">
   ''' + errors_html + '''
</div> 
        <p class="thick">MFA information</p><br>
                <button type="button" class="collapsible">Click to show MFA information</button>
<div class="content">
   ''' + mfa_html + '''
</div> 
    
    </body>
    <script>
var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
  });
}
</script>
</html>'''

        #fw = open(r"report.html", encoding="utf8")
        #fw.write(html_string)
        #fw.close()
        with open(r"report.html", 'w', encoding = 'utf8') as fw:
            fw.write(html_string)
