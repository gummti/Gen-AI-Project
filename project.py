import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import boto3
import time
from typing import Optional
# avanti add
# Bedrock Setup
def get_bedrock_client(
    runtime: Optional[bool] = True,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None
):
    service_name = 'bedrock-runtime' if runtime else 'bedrock'
    return boto3.client(
        service_name=service_name,
        region_name="us-west-2",  # Change if needed
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

# Web scraping
def extract_text_from_html(url):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        # Remove common non-content elements
        for tag in soup(["script", "style", "meta", "noscript", "header", "footer", "nav", "form", "aside"]):
            tag.decompose()

        # Check for body existence
        if not soup.body:
            return "Error: No <body> tag found in the HTML"

        text = soup.body.get_text(separator="\n", strip=True)

        # Clean lines
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        clean_text = "\n".join(lines)

        # Optional: Save to file for inspection
        # with open("debug_scraped_text.txt", "w", encoding="utf-8") as f:
        #     f.write(clean_text)

        return clean_text

    except Exception as e:
        return f"Error: {e}"

# Heuristic: Detect type of civic document based on keywords
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

def summarize_text_with_bedrock(text, model_id="anthropic.claude-v2", max_tokens=1000):
    page_type = detect_page_type(text)
    print("Detected page type:", page_type)

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


# Streamlit UI
st.title("SLO County Civic Info Summarizer")

st.write("""
This tool summarizes government or public policy information for San Luis Obispo County. Choose how you'd like to get started:
""")

option = st.radio("Choose an option:", [
    "Enter a government or policy webpage URL",
    "Pick a topic to explore current news in SLO county"
])

if option == "Enter a government or policy webpage URL":
    url = st.text_input("Enter the URL:")
    if url and st.button("Extract and Summarize"):
        with st.spinner("Scraping and summarizing..."):
            text = extract_text_from_html(url)
            if text.startswith("Error:"):
                st.error(text)
            else:
                summary = summarize_text_with_bedrock(text)
                st.success("Summarized successfully!")
                st.subheader("Summary:")
                st.write(summary)

elif option == "Pick a topic to explore current news in SLO county":
    st.write("Select a topic below:")

    topics = {
        "Clerk-Recorder": "https://www.slocounty.ca.gov/departments/clerk-recorder/news-announcements",
        "Upcoming Elections": "https://www.slocounty.ca.gov/departments/clerk-recorder/all-services/elections-and-voting/current-upcoming-elections",
        "Public Health": "https://www.slocounty.ca.gov/departments/health-agency/public-health/department-news",
        "Auditor - Controller - Treasurer": "https://www.slocounty.ca.gov/departments/auditor-controller-treasurer-tax-collector-public/news"
    }

    for label, link in topics.items():
        if st.button(label):
            with st.spinner(f"Loading {label}..."):
                text = extract_text_from_html(link)
                if text.startswith("Error:"):
                    st.error(text)
                else:
                    summary = summarize_text_with_bedrock(text)
                    st.success("Summarized successfully!")
                    st.subheader(f"Summary for: {label}")
                    st.write(summary)
