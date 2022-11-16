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
    def __init__(self, sus, groups, roles, initiated, target, signin):
        self.sus = sus
        self.groups = groups
        self.roles = roles
        self.initiated = initiated
        self.target = target
        self.signin = signin

    def create_roles_string(self):
        if self.roles == "This user has no roles.":
            return self.roles
        roles_string = ""
        for role in self.roles:
            roles_string += role + "<br>"

        return roles_string

    def create_groups_output(self):
        if self.groups == "This user is not a member of any group.":
            return self.groups
        groups_df = pd.DataFrame(data=self.groups)
        groups_html = groups_df.style.to_html(classes='table table-stripped')
        return groups_html

    def generate_report(self):
        groups_html = self.create_groups_output()
        roles_html = self.create_roles_string()
        if self.sus['onPremisesSyncEnabled']:
            sync_data = f"SID: {self.sus['onPremisesSecurityIdentifier']}, UserPrincipalName: {self.sus['onPremisesUserPrincipalName']}"
        else:
            sync_data = "User is not synced."
        
        if self.initiated == "This user has not performed any action.":
            initiated_html = self.initiated
        else:
            with open(r"report_initiated.html", 'r') as f:
                initiated_html = f.read()
        
        if self.target == "No operations have been performed on this user.":
            target_html = self.target
        else:
            with open(r"report_target.html", 'r') as f:
                target_html = f.read()

        if self.signin == "This user has not logged in.":
            sigin_html = self.signin
        else:
            with open(r"report_signin.html", 'r') as f:
                sigin_html = f.read()
        
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
        </style>
    </head>
    
    <body>
        <img src="logo.png" width="150" height="50">
        <!-- *** Section 0 *** --->
        <section>
        <h3>User details:</h3>
        <p class="thick">Id:</p> ''' + self.sus['id'] + '''<br>
        <p class="thick">DisplayName:</p> ''' + self.sus['displayName'] + '''<br>
        <p class="thick">UserPrincipalName:</p> ''' + self.sus['userPrincipalName'] + '''<br>
        <p class="thick">OnPremises:</p> ''' + sync_data + '''<br>
        <p class="thick">Created:</p> ''' + self.sus['createdDateTime'] + '''<br>
        <p class="thick">Groups:</p><br>
        <button type="button" class="collapsible">Click to show groups</button>
<div class="content">
   ''' + groups_html + '''
</div>
        <p class="thick">Roles:</p><br>
        <button type="button" class="collapsible">Click to show roles</button>
<div class="content">
   ''' + roles_html + '''
</div>  
        </section>
        <!-- *** Section 1 *** --->
        <h2>Initiated Activities:</h2>
        ''' + initiated_html + '''

        <!-- *** Section 2 *** --->
        <h2>Activities as target:</h2>
        ''' + target_html + '''

        <!-- *** Section 2 *** --->
        <h2>User sign-in graph:</h2>
        ''' + sigin_html + '''

    
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

        with open(r"report.html", 'w', encoding = 'utf8') as fw:
            fw.write(html_string)
