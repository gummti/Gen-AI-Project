# Gen-AI SLO County Policy & Government Navigator

## Overview
The Gen-AI SLO County Policy & Government Navigator is an AI-powered tool designed to make local government information more accessible, digestible, and actionable. Built specifically for San Luis Obispo County, the tool scrapes content from official local government websites — such as the Board of Supervisors, Elections, and department news pages — and uses large language models to generate plain-language summaries for the public.

The prototype features a Streamlit-based interface where users can:

1. Paste a government webpage URL to receive an AI-generated summary of that page

2. Explore by topic using a dropdown of known SLO County departments and services

3. Receive plain-English briefings on policies, decisions, deadlines, and public actions

4. Summarize embedded links within the original page (e.g., supporting documents, department pages)

By combining web scraping, natural language processing, and a lightweight UI, the Navigator lowers barriers to civic engagement — especially for students, organizers, and community members who may not have time to track local government updates across scattered websites and formats.

## Team Members
- Avanti Gummaraju
- Paige Tsai

## How to Use
1. Clone the repo:
   
git clone https://github.com/YOUR_USERNAME/Gen-AI-Project.git

cd Gen-AI-Project

2. Install requirements:
   
pip install -r requirements.txt

3. Run the Streamlit app:
   
streamlit run app.py

## Dependencies
See `requirements.txt`. Major packages include:

- streamlit
- beautifulsoup4
- requests
- boto3

## Notes
This app uses Claude v2 via Amazon Bedrock, so you’ll need AWS credentials and proper setup to access the model.
