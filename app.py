import streamlit as st
import pandas as pd
import gspread
import os
import requests
from google.oauth2.service_account import Credentials
from openai import OpenAI
import config
import time


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = config.SERVICE_ACCOUNT_FILE  # Update with your file path
SPREADSHEET_ID = config.SPREADSHEET_ID
api_key = os.getenv("OPENAI_API_KEY")
RESUME_FILE = "resume.txt"  # File containing your resume details
EMAIL_SCRIPT_URL = config.EMAIL_SCRIPT_URL  # Web App URL for email sending script

def get_google_sheet_data():
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1  # Get first sheet
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df, sheet
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None, None
    
def load_resume():
    try:
        with open(RESUME_FILE, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        st.error(f"Resume file '{RESUME_FILE}' not found. Please create this file with your resume details.")
        return None
    
    
def generate_skill_alignment(job_desc, resume_details):
    prompt = f"""
    Given the following job description and my resume details, generate a short summary of how my skills align with the role.

    Job Description:
    {job_desc}

    My Resume Details:
    {resume_details}

    Output should be a concise, professional summary continuing from: 'Grant has an experience in ...'. 
    The response should be **a single sentence** with a maximum of 14 words, but do not include "Grant has an experience in" in your response, include what comes after it.
    Your goal is NOT to overgeneralize like saying ("software engineering, collaborating on cross-functional teams, and implementing scalable, high-quality solutions"), but rather 
    include the actual technical skills, languages, and frameworks. Be very detailed and technically dense. Make sure there is no period and no punctuation in the end of your output.
    Lastly since you are listing skills with commas, make sure to insert and between last and second to last skill so it sounds natural.
    """

    try:
        # Initialize OpenAI client
        client = OpenAI()

        # API request
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        # Extract response text
        response_text = completion.choices[0].message.content.strip()
        return response_text
    except Exception as e:
        st.error(f"Error fetching output from OpenAI: {e}")
        return ""

# Function to generate recruiter email
def generate_email(recruiter_name, position, date_applied, company_name, skill_alignment):
    if not recruiter_name or recruiter_name.strip() == "":
        return ""

    email_template = f"""Hi {recruiter_name},
    
I hope all is well. My name is Grant Ovsepyan and I applied for {position} position on {date_applied}. I am truly interested in {company_name} and I believe I am a good fit for {position} position since I have experience in {skill_alignment}. Would you be able to connect me with one of the engineers, so I can learn more about the nature of work and work culture better? 
Thank you for reading this email.

All the Best,  
Grant Ovsepyan"""
    
    return email_template

# Streamlit UI
st.title("Google Sheets Email Automation & Status Monitor")

# Load resume once into session state
if "resume_details" not in st.session_state:
    st.session_state.resume_details = load_resume()

# Initialize session state variables
if "df" not in st.session_state:
    st.session_state.df = None
if "sheet" not in st.session_state:
    st.session_state.sheet = None
if "show_df" not in st.session_state:
    st.session_state.show_df = False


# Button: Show Excel as DataFrame
if st.button("Show Excel as DF"):
    df, sheet = get_google_sheet_data()
    if df is not None:
        st.session_state.df = df
        st.session_state.sheet = sheet
        st.session_state.show_df = True

# Button: Close Excel as DataFrame
if st.button("Close Excel as DF"):
    st.session_state.show_df = False

# Display DataFrame if toggled on
if st.session_state.show_df and st.session_state.df is not None:
    st.write("### Google Sheets Data:")
    st.dataframe(st.session_state.df)

# Button: Populate Skill Alignment
if st.button("Populate Skill Alignment"):
    if st.session_state.df is None:
        st.error("Load the spreadsheet first by clicking 'Show Excel as DF'.")
    elif not st.session_state.resume_details:
        st.error("Resume file not found. Please create 'resume.txt' with your details.")
    else:
        df = st.session_state.df.copy()
        sheet = st.session_state.sheet

        updates = []
        for index, row in df.iterrows():
            if row["skill_alignment"].strip() == "":  # If skill_alignment is empty
                job_desc = row["job_description"]
                generated_text = generate_skill_alignment(job_desc, st.session_state.resume_details)

                if generated_text:
                    df.at[index, "skill_alignment"] = generated_text
                    updates.append((index + 2, df.columns.get_loc("skill_alignment") + 1, generated_text))

        # Batch update Google Sheet
        if updates:
            for row, col, value in updates:
                sheet.update_cell(row, col, value)

            # Update Streamlit DataFrame
            st.session_state.df = df
            st.success(f"Skill Alignment updated for {len(updates)} rows!")

            # Show updated DataFrame
            st.write("### Updated Data:")
            st.dataframe(st.session_state.df)
        else:
            st.warning("No rows needed updating.")

# Button: Populate Emails
if st.button("Populate Emails"):
    if st.session_state.df is None:
        st.error("Load the spreadsheet first by clicking 'Show Excel as DF'.")
    else:
        df = st.session_state.df.copy()
        sheet = st.session_state.sheet

        updates = []
        for index, row in df.iterrows():
            for recruiter_col, email_col, email_field in [
                ("recruiter1", "entire_email1", "recruiter1_email"),
                ("recruiter2", "entire_email2", "recruiter2_email"),
                ("recruiter3", "entire_email3", "recruiter3_email"),
            ]:
                recruiter_name = row[recruiter_col].strip() if pd.notna(row[recruiter_col]) else ""
                position = row["position"].strip() if pd.notna(row["position"]) else ""
                date_applied = row["date_applied"].strip() if pd.notna(row["date_applied"]) else ""
                company_name = row["company_name"].strip() if pd.notna(row["company_name"]) else ""
                skill_alignment = row["skill_alignment"].strip() if pd.notna(row["skill_alignment"]) else ""
                recruiter_email = row[email_field].strip() if pd.notna(row[email_field]) else ""

                # Ensure all required fields + recruiter email exist before generating the email
                if all([recruiter_name, position, date_applied, company_name, skill_alignment, recruiter_email]):
                    generated_email = generate_email(recruiter_name, position, date_applied, company_name, skill_alignment)

                    if generated_email:
                        df.at[index, email_col] = generated_email
                        updates.append((index + 2, df.columns.get_loc(email_col) + 1, generated_email))
                else:
                    # If required fields or email are missing, leave the email field empty
                    df.at[index, email_col] = ""

        # Batch update Google Sheet
        if updates:
            for row, col, value in updates:
                sheet.update_cell(row, col, value)

            # Update Streamlit DataFrame
            st.session_state.df = df
            st.success(f"Emails populated for {len(updates)} recruiters!")

            # Show updated DataFrame
            st.write("### Updated Data:")
            st.dataframe(st.session_state.df)
        else:
            st.warning("No emails were populated due to missing required information.")

# Button: Show Missing Emails (Placed Right After "Populate Emails")
if st.button("Show Missing Emails"):
    if st.session_state.df is None:
        st.error("Load the spreadsheet first by clicking 'Show Excel as DF'.")
    else:
        # Re-fetch data
        df, sheet = get_google_sheet_data()
        if df is not None:
            st.session_state.df = df
            # Filter rows with at least one missing `entire_emailX`
            missing_email_rows = df[
                (df["entire_email1"].isna()) | (df["entire_email1"].str.strip() == "") |
                (df["entire_email2"].isna()) | (df["entire_email2"].str.strip() == "") |
                (df["entire_email3"].isna()) | (df["entire_email3"].str.strip() == "")
            ]
            # Count total missing email fields
            total_missing = (
                df["entire_email1"].isna().sum() + (df["entire_email1"].str.strip() == "").sum() +
                df["entire_email2"].isna().sum() + (df["entire_email2"].str.strip() == "").sum() +
                df["entire_email3"].isna().sum() + (df["entire_email3"].str.strip() == "").sum()
            )

            st.write(f"### Rows where at least one email is missing ({total_missing} total missing emails across all rows):")
            st.dataframe(missing_email_rows)


# Send Emails
if st.button("Send Emails"):
    if st.session_state.df is None:
        st.error("Load the spreadsheet first by clicking 'Show Excel as DF'.")
    else:
        df = st.session_state.df.copy()
        sheet = st.session_state.sheet

        # Mark unsent as "Pending"
        updates = []
        for index, row in df.iterrows():
            for recruiter_col, email_col, sent_col in [
                ("recruiter1", "entire_email1", "sent1"),
                ("recruiter2", "entire_email2", "sent2"),
                ("recruiter3", "entire_email3", "sent3"),
            ]:
                # If not successful and we have an email body
                if row[sent_col] != "Successful" and row[email_col].strip() != "":
                    updates.append((index + 2, df.columns.get_loc(sent_col) + 1, "Pending"))

        if updates:
            for (row_num, col_num, val) in updates:
                sheet.update_cell(row_num, col_num, val)

            st.success("Emails set to 'Pending'... Now calling Apps Script to send them 1/6 sec.")
            # Call the script
            try:
                response = requests.get(EMAIL_SCRIPT_URL)
                st.write("Status Code:", response.status_code)
                st.write("Response Text:", response.text)
            except Exception as e:
                st.error(f"Error calling Apps Script: {e}")

            # Optionally re-fetch after some wait
            # But we can just reload if we want:
            df, sheet = get_google_sheet_data()
            st.session_state.df = df
            st.write("### Updated Data:")
            st.dataframe(df)
        else:
            st.warning("No emails need sending.")


# 6. Additional Buttons: Filter Rows by Status

if st.session_state.sheet is not None:
    # Button: Show All Successful
    if st.button("Show All Successful"):
        # Re-fetch data from Google Sheets
        df, sheet = get_google_sheet_data()
        if df is not None:
            st.session_state.df = df
            # Filter rows with at least one "Successful"
            successful_rows = df[
                (df["sent1"] == "Successful") |
                (df["sent2"] == "Successful") |
                (df["sent3"] == "Successful")
            ]
            # Count total successful emails
            total_successful = (
                (df["sent1"] == "Successful").sum() +
                (df["sent2"] == "Successful").sum() +
                (df["sent3"] == "Successful").sum()
            )

            st.write(f"### Rows where at least one email is Successful ({total_successful} total emails sent successfully):")
            st.dataframe(successful_rows)

    # Button: Show Any Pending
    if st.button("Show Any Pending"):
        # Re-fetch data
        df, sheet = get_google_sheet_data()
        if df is not None:
            st.session_state.df = df
            # Filter rows with at least one "Pending"
            pending_rows = df[
                (df["sent1"] == "Pending") |
                (df["sent2"] == "Pending") |
                (df["sent3"] == "Pending")
            ]
            # Count total pending emails
            total_pending = (
                (df["sent1"] == "Pending").sum() +
                (df["sent2"] == "Pending").sum() +
                (df["sent3"] == "Pending").sum()
            )

            st.write(f"### Rows where at least one email is Pending ({total_pending} total emails still pending):")
            st.dataframe(pending_rows)

    # Button: Show Any Failed
    if st.button("Show Any Failed"):
        # Re-fetch data
        df, sheet = get_google_sheet_data()
        if df is not None:
            st.session_state.df = df
            # Filter rows with at least one "Failed"
            failed_rows = df[
                (df["sent1"] == "Failed") |
                (df["sent2"] == "Failed") |
                (df["sent3"] == "Failed")
            ]
            # Count total failed emails
            total_failed = (
                (df["sent1"] == "Failed").sum() +
                (df["sent2"] == "Failed").sum() +
                (df["sent3"] == "Failed").sum()
            )

            st.write(f"### Rows where at least one email is Failed ({total_failed} total emails failed to send):")
            st.dataframe(failed_rows)
