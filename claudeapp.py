import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import boto3
import time
from typing import Optional

# Set up Streamlit page configuration
st.set_page_config(
    page_title="SLO County Policy Navigator",
    page_icon="🗳️",
    layout="wide"
)

# Custom CSS styling for NPR-style UI
st.markdown("""
<style>
body, div, p, label, input, textarea {
    font-family: 'Georgia', serif !important;
    font-size: 16px;
    color: #2c2c2c;
}
h1, h2, h3, h4 {
    font-family: 'Georgia', serif !important;
    color: #1A1A1A;
}
section.main > div {
    padding: 2rem 3rem;
    background-color: #ffffff;
    border: 1px solid #e2e2e2;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0,0,0,0.05);
    margin-bottom: 2rem;
}
.stButton > button {
    background-color: #003262;
    color: white;
    font-weight: bold;
    border: none;
    border-radius: 4px;
    padding: 0.5rem 1rem;
}
.stButton > button:hover {
    background-color: #005288;
}
input, textarea {
    border-radius: 4px;
    border: 1px solid #ccc;
    padding: 0.5rem;
    margin-top: 0.2rem;
}
.stRadio > div, .stSelectbox > div {
    background-color: #fafafa;
    border-radius: 5px;
    padding: 1rem;
    border: 1px solid #e0e0e0;
}
.stSpinner {
    color: #003262;
}
</style>
""", unsafe_allow_html=True)

# Bedrock client setup
def get_bedrock_client(
    runtime: Optional[bool] = True,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None
):
    service_name = 'bedrock-runtime' if runtime else 'bedrock'
    return boto3.client(
        service_name=service_name,
        region_name="us-west-2",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token
    )

bedrock_runtime = get_bedrock_client()

def invoke_model(body, model_id, accept, content_type):
    try:
        start_time = time.time()
        response = bedrock_runtime.invoke_model(
            body=json.dumps(body),
            modelId=model_id,
            accept=accept,
            contentType=content_type
        )
        result = json.loads(response['body'].read().decode('utf-8'))
        print(f"Inference took {time.time() - start_time:.2f} seconds")
        return result
    except Exception as e:
        return f"Error invoking model: {e}"

# Scrape and clean webpage text
def extract_text_from_html(url):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "meta", "noscript", "header", "footer", "nav", "form", "aside"]):
            tag.decompose()
        if not soup.body:
            return "Error: No <body> tag found in the HTML"
        text = soup.body.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"

# Heuristically detect document type
def detect_page_type(text):
    lowered = text.lower()
    if "agenda" in lowered or "meeting" in lowered:
        return "meeting agenda"
    elif "budget" in lowered or "fiscal" in lowered:
        return "budget report"
    elif "school board" in lowered:
        return "school board report"
    elif "ordinance" in lowered or "resolution" in lowered:
        return "policy or law proposal"
    else:
        return "general government page"

# Generate summary using Bedrock Claude
def summarize_text_with_bedrock(text, model_id="anthropic.claude-v2", max_tokens=1000):
    page_type = detect_page_type(text)
    instruction = f"""You are a helpful civic engagement assistant. Please summarize the following {page_type} content for a general audience.
Focus on dates, deadlines, events, decisions, public actions, or policy announcements.
Keep the tone neutral and informative. Avoid unnecessary repetition or generalities.
"""
    prompt = f"""Human: {instruction}
--- START OF CONTENT ---
{text}
--- END OF CONTENT ---
Assistant:"""
    body = {
        "prompt": prompt,
        "max_tokens_to_sample": max_tokens,
        "temperature": 0.3,
        "stop_sequences": ["Human:"]
    }
    result = invoke_model(
        body=body,
        model_id=model_id,
        accept="application/json",
        content_type="application/json"
    )
    if isinstance(result, dict):
        return result.get("completion", "").strip()
    else:
        return f"[Error] {result}"

# Banner
st.markdown("""
<div style="background-color:#003262;padding:1rem 2rem;border-radius:6px;margin-bottom:2rem;">
  <h2 style="color:white;margin:0;">SLO County Policy & Government Navigator</h2>
  <p style="color:white;margin:0.2rem 0 0 0;">Powered by AI tools for public transparency and civic understanding.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("###Explore Civic Information")
st.write("This tool helps you understand public documents and policy updates in **plain language**. Choose how to begin:")

option = st.radio("Choose an option:", [
    "Enter a government or policy webpage URL",
    "Pick a topic to explore current news in SLO County"
])

# Option 1: Enter URL
if option == "Enter a government or policy webpage URL":
    url = st.text_input("Paste the URL of a government page:")
    if url and st.button("Extract and Summarize"):
        with st.spinner("Scraping and summarizing..."):
            text = extract_text_from_html(url)
            if text.startswith("Error:"):
                st.error(text)
            else:
                summary = summarize_text_with_bedrock(text)
                st.success("Summary complete.")
                st.subheader("Summary:")
                st.write(summary)

# Option 2: Pick a predefined topic
elif option == "Pick a topic to explore current news in SLO County":
    st.write("Select a department or topic:")
    topics = {
        "Clerk-Recorder": "https://www.slocounty.ca.gov/departments/clerk-recorder/news-announcements",
        "Upcoming Elections": "https://www.slocounty.ca.gov/departments/clerk-recorder/all-services/elections-and-voting/current-upcoming-elections",
        "Public Health": "https://www.slocounty.ca.gov/departments/health-agency/public-health/department-news",
        "Auditor - Controller - Treasurer": "https://www.slocounty.ca.gov/departments/auditor-controller-treasurer-tax-collector-public/news"
    }

    for label, link in topics.items():
        if st.button(label):
            with st.spinner(f"Loading and summarizing content from {label}..."):
                text = extract_text_from_html(link)
                if text.startswith("Error:"):
                    st.error(text)
                else:
                    summary = summarize_text_with_bedrock(text)
                    st.success("Summary complete.")
                    st.subheader(f"Summary for: {label}")
                    st.write(summary)