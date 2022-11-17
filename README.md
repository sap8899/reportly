
![logo2](https://user-images.githubusercontent.com/88736901/202279693-ff033711-8e8d-4004-a976-49d50c82cb70.png)

Reportly is an AzureAD user activity report tool.

# About the tool
This is a tool that will help blue teams during a cloud incident.
When running the tool, the researcher will enter as input a suspicious user and a time frame and will receive a report detailing the following: 
1. Information about the user 
2. Actions taken by the user 
3. Actions taken on the user 
4. User login and failure logs


https://user-images.githubusercontent.com/88736901/202284687-9862e097-a5d6-4557-a474-d99e37269c2e.mp4


# Usage
Insert User principal name of a suspicious user.<br>
Insert start and end times in the following format: 2022-11-16<br>
**I recommend a range of no longer then a week.**

The reports are created in the executable's directory.

# Installation
In order to use the tool you will need an AzureAD application with the following **delegated** microsoft graph api permissions:<br>
* AuditLog.Read.All<br>
* GroupMember.Read.All<br>
* RoleManagement.Read.Directory<br>
* User.Read<br>
* User.Read.All<br>
<br>**dont forget to grant admin consent**
![image](https://user-images.githubusercontent.com/88736901/202277163-5ee21b25-397c-4132-8598-de53d9ae168d.png)
<br>
To create an application go to "App registration" tab and select "New registration" option.
![image](https://user-images.githubusercontent.com/88736901/202480881-6ad5c099-8ff5-4e26-b88d-6dfac4a360c1.png)


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
