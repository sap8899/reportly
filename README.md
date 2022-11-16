# Reportly
Reportly is an AzureAD user activity report tool.

# About the tool
This is a tool that will help blue teams during a cloud incident.
When running the tool, the researcher will enter as input a suspicious user and a time frame and will receive a report detailing the following: 
1. Information about the user 
2. Actions taken by the user 
3. Actions taken on the user 
4. User login and failure logs

# Usage
Insert User principal name of a suspicious user.<br>
Insert start and end times in the following format: 2022-11-16<br>
**I recommend a range of no longer then a week.**

# Installation
In order to use the tool you will need an AzureAD application with the following **delegated** microsoft graph api permissions:<br>
* AuditLog.Read.All<br>
* GroupMember.Read.All<br>
* RoleManagement.Read.Directory<br>
* User.Read<br>
* User.Read.All<br>
**dont forget to grant admin consent**
![image](https://user-images.githubusercontent.com/88736901/202277163-5ee21b25-397c-4132-8598-de53d9ae168d.png)

Add a secret to the application.

After you created the application you need to fill the config.cfg file:<br>
clientId = application id<br>
clientSecret = application secret<br>
tenantId = tenant id<br>
