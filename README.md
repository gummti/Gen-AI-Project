# Gen-AI SLO County Policy & Government Navigator

## Overview
The Gen-AI SLO County Policy & Government Navigator is an AI-powered tool designed to make local government information more accessible and understandable for the public. Built specifically for San Luis Obispo County, the tool scrapes agendas, public records, and announcements from local government websites—such as city councils, school boards, and Cal Poly's ASI—then uses large language models to summarize and contextualize that information in a clear, conversational format.

The prototype features a Streamlit-based interface where users can:

1. Explore recent government documents and summaries

2. Search or filter by topic, department, or date

3. Receive AI-generated briefings on policy developments

4. Interact with linked resources and generate summaries of embedded URLs

By combining web scraping, natural language processing, and an intuitive interface, the Navigator aims to lower barriers to civic engagement and support informed participation in local governance—especially for students and community members who may not regularly follow public meetings or government portals.

## Team Members
- Avanti Gummaraju
- Paige Tsai

## How to Use
1. Clone the repo:
   
git clone https://github.com/YOUR_USERNAME/Gen-AI-Project.git

cd Gen-AI-Project

3. Install requirements:
   
pip install -r requirements.txt

5. Run the Streamlit app:
   
streamlit run app.py

## Dependencies
See `requirements.txt`.

## Notes
This app uses Claude via Amazon Bedrock, so you’ll need AWS credentials and proper setup to access the model.
