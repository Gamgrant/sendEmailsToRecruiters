# sendEmailsToRecruiters
automate the process of reaching out to recruiters with google spreadsheet
1. Enable Google Sheets API & Create a Service Account
Follow these steps:

Step 1: Create a Google Cloud Project
Go to Google Cloud Console.
Click "Select a project" (or "Create a project" if none exist).
Name your project (e.g., GoogleSheetsApp).
Click "Create".
Step 2: Enable Google Sheets API
In Google Cloud Console, search for "Google Sheets API".
Click Enable.
Step 3: Create a Service Account
In Google Cloud Console, go to IAM & Admin → Service Accounts.
Click "Create Service Account".
Name it (e.g., sheets-access), then click "Create & Continue".
Grant no roles (not needed).
Click "Done".
Step 4: Generate JSON Credentials
In the Service Accounts list, find the one you created.
Click on it, then go to "Keys".
Click "Add Key" → "Create New Key".
Select JSON format.
Click Create → A credentials.json file will be downloaded.
Step 5: Move credentials.json to Your Project Folder
Move the credentials.json file to the same folder as your app.py file.
If using a different directory, update the path in your script.
2. Set Up the SCOPES Variable
The SCOPES define the level of access to Google Sheets. This line is correct:

python
Copy
Edit
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
This allows read and write access to Google Sheets.

3. Share the Google Sheet with the Service Account
Your service account needs access to the Google Sheet.

Open your Google Sheet.

Click "Share" (top-right).

Copy the email from the credentials.json file. It will look like:

perl
Copy
Edit
my-service-account@my-project.iam.gserviceaccount.com
Paste this email in the "Share" field.

Set access to "Editor" and click "Send".

Now your service account can access the spreadsheet.

