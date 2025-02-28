# sendEmailsToRecruiters

## Project Description
Automates recruiter outreach based on job applications in Google Sheets. Uses Streamlit for UI and Google Apps Script for automated email sending, ensuring proper spacing to avoid spam detection.
```
├── README.md
├── app.py
├── credentials.json
├── config.py
├── resume.txt
└── testing.ipynb
```
Your config.py shoud have the following vars:

```python
SERVICE_ACCOUNT_FILE = "blah-blah-blah"  
SPREADSHEET_ID = "blah-blah-blah"
EMAIL_SCRIPT_URL = "blah-blah-blah"
```
## Features
### 📊 Fetch & Display Google Sheets Data
- **Show Excel as DF**: Load job applications into Streamlit DataFrame.
- **Close Excel as DF**: Hide DataFrame.

### 🤖 Automate Skill Alignment
- **Populate Skill Alignment**: Uses GPT-4o to fill missing skill summaries based on job descriptions.
- Updates Google Sheet with generated values.

### ✉️ Generate Personalized Emails
- **Populate Emails**: Creates recruiter outreach emails if empty.
- Updates Google Sheet with generated emails.

### 🚀 Automated Email Sending (via Google Apps Script)
- Marks emails as "Pending" and triggers Apps Script:
  - Sends **one email per minute**.
  - Updates status to "Successful" or "Failed".

### 🔍 Filter & Monitor Email Status
- **Show All Successful**: Emails marked "Successful".
- **Show Any Pending**: At least one email "Pending".
- **Show Any Failed**: At least one email "Failed".

## ⚙️ Tech Stack
- **Frontend**: Streamlit (Python)
- **Backend**: Google Apps Script (for email sending)
- **AI Integration**: GPT-4o (OpenAI API)
- **Data Storage**: Google Sheets

## 🛠 Setup
* your spreadsheet header should look like this, make sure to have 3 recruiter emails per company.
| recruiter1 | recruiter1_email | recruiter2 | recruiter2_email | recruiter3 | recruiter3_email | company_name | position | job_description | date_applied | skill_alignment | entire_email1 | entire_email2 | entire_email3 | sent1 | sent2 | sent3 |
|------------|-----------------|------------|-----------------|------------|-----------------|--------------|---------|----------------|-------------|----------------|--------------|--------------|--------------|------|------|------|

### 1️⃣ Enable Google Sheets API & Create Service Account
1. **Create Google Cloud Project**: Google Cloud Console → "Select a project" → Name it.
2. **Enable Google Sheets API**: Search "Google Sheets API" → Click "Enable".
3. **Create Service Account**: IAM & Admin → Service Accounts → "Create Service Account" → Skip roles → Click "Done".
4. **Generate JSON Credentials**: Service Accounts → Keys → "Add Key" → "Create New Key" (JSON format).
5. **Move Credentials File**: Place `credentials.json` in the project folder, add to `config.py`:
   ```python
   SERVICE_ACCOUNT_FILE = "credentials.json"
   ```
6. **Share Google Sheet with Service Account**: Copy email from `credentials.json`, share with "Editor" access.
7. **Get Spreadsheet ID**: Copy from URL after `d/` and save in `config.py`:
   ```python
   SPREADSHEET_ID = "your_spreadsheet_id"
   ```

### 2️⃣ Configure OpenAI API Key
- Generate API key from OpenAI → Add to Conda environment:
  ```sh
  vim ~/anaconda3/envs/<your_env>/etc/conda/activate.d/env_vars.sh
  ```
- Verify:
  ```sh
  conda deactivate && conda activate <your_env>
  echo $OPENAI_API_KEY
  ```

### 3️⃣ Google Apps Script for Email Sending
1. **Open Google Sheets** → Extensions → Apps Script → Replace with:
   ```javascript
   function sendEmailsFromSheet() {
     var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Sheet1");
     var data = sheet.getDataRange().getValues();
     var header = data[0];
     var recruiterEmailCols = ["recruiter1_email", "recruiter2_email", "recruiter3_email"];
     var emailCols = ["entire_email1", "entire_email2", "entire_email3"];
     var sentCols = ["sent1", "sent2", "sent3"];
     var startTime = new Date().getTime();
     var totalEmailsSent = 0;

     for (var i = 1; i < data.length; i++) {
       for (var j = 0; j < recruiterEmailCols.length; j++) {
         var email = data[i][header.indexOf(recruiterEmailCols[j])];
         var content = data[i][header.indexOf(emailCols[j])];
         var sentStatus = data[i][header.indexOf(sentCols[j])];

         if (email && content && sentStatus == "Pending") {
           try {
             MailApp.sendEmail({to: email, subject: "Application Follow-Up", body: content});
             sheet.getRange(i + 1, header.indexOf(sentCols[j]) + 1).setValue("Successful");
             totalEmailsSent++;
             Utilities.sleep(6000);
             if (new Date().getTime() - startTime >= 350000) return;
           } catch (err) {
             sheet.getRange(i + 1, header.indexOf(sentCols[j]) + 1).setValue("Failed");
           }
         }
       }
     }
   }
   ```
2. **Deploy** → New Web Deployment → Set access to "Anyone".
3. **Copy Web URL** → Add to `config.py`:
   ```python
   EMAIL_SCRIPT_URL = "your_script_url"
   ```

### 4️⃣ Running the Project
```sh
streamlit run app.py
```

## 🎯 Key Benefits
✅ Automates recruiter outreach efficiently.  
✅ Prevents spam detection with controlled email sending.  
✅ Runs on Google’s infrastructure (no server needed).  
✅ No need to keep the app open while sending emails.  
