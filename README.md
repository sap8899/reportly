

![logo](https://github.com/sap8899/reportly/assets/88736901/9a1d58a9-2e21-4e75-982c-4eb3950f2ed5)


Reportly is an EntraID user activity report tool.

# About the tool
This is a tool that will help blue teams during a cloud incident.
When running the tool, the researcher will enter as input a suspicious user and a time frame and will receive a report detailing the following: 
1. Information about the user 
2. Actions taken by the user 
3. Actions taken on the user 
4. User login and failure logs


# Usage
When running the tool, a link to authentication and a device code will show, follow the link and enter the code to authenticate.
![image](https://github.com/sap8899/reportly/assets/88736901/80428e0d-e566-4b9d-897f-a0b7d0567a35)

Insert User principal name of a suspicious user.<br>
Insert start and end times in the following format: 2022-11-16<br>
**I recommend a range of no longer than a week.**

When the report will be ready the tool will print "Your report is ready!".
The reports are created in the executable's directory by default.

**Attached an example report "report_example.html"**

# Installation
In order to use the tool you will need an EntraID application with the following **delegated** microsoft graph api permissions:<br>
* AuditLog.Read.All<br>
* GroupMember.Read.All<br>
* RoleManagement.Read.Directory<br>
* User.Read<br>
* User.Read.All<br>
<br>**dont forget to grant admin consent**
![image](https://user-images.githubusercontent.com/88736901/202277163-5ee21b25-397c-4132-8598-de53d9ae168d.png)
<br>
To create an application go to "App registration" tab and select "New registration" option.

![image](https://user-images.githubusercontent.com/88736901/202481694-979c2dd3-7484-4e65-ba17-9298701a1ca1.png)


<br>Also, when creating the application, make sure you mark the following option as "yes":
![image](https://user-images.githubusercontent.com/88736901/202479500-fd0e5ebf-c4bd-4745-a0dc-8057e39d51cf.png)
* you can find this property under the application's "Authentication" tab.

<br>Add a secret to the application.
![image](https://user-images.githubusercontent.com/88736901/202480440-4bc20d18-ba90-491d-885a-049126d29e45.png)

* Go to "Certificates & secrets"
* Add a secret
* Immediately copy the secret to the config file (after you watch it once, it disappears)

After you created the application you need to fill the config.cfg file:<br>
clientId = application id<br>
clientSecret = application secret<br>
tenantId = tenant id<br>
