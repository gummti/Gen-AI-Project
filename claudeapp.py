import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import boto3
import time
from typing import Optional

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
    
def extract_links_from_html(url):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        base_url = "/".join(url.split("/")[:3])
        links = []

        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            if href.startswith("/"):
                href = base_url + href  # make relative links absolute
            elif not href.startswith("http"):
                continue  # skip mailto, javascript, etc.
            text = tag.get_text(strip=True)
            if text and href not in [l["url"] for l in links]:
                links.append({"text": text, "url": href})

        return links
    except Exception as e:
        return []

def find_link_by_text(links, keyword):
    keyword = keyword.lower()
    for link in links:
        if keyword in link["text"].lower() or keyword in link["url"].lower():
            return link["url"]
    return None


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
import streamlit as st

# --- Page Setup ---
st.set_page_config(page_title="LocalGov Navigator", layout="wide")

# --- Custom CSS Styling ---
st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: 'Georgia', 'Merriweather', serif;
        }

        .gov-header {
            display: flex;
            align-items: center;
            background-color: #2B2E4A;
            color: white;
            padding: 1rem 2rem;
            border-bottom: 4px solid #BFE3D2;
        }

        .gov-title {
            font-size: 30px;
            font-weight: 700;
            margin-left: 15px;
        }

        .section {
            margin-top: 2.5rem;
        }

        .summary-box {
            background-color: #f7f7f7;
            border-left: 5px solid #2B2E4A;
            padding: 1.2rem;
            font-size: 16px;
            margin-top: 1rem;
        }

        .footer {
            text-align: center;
            color: #888;
            font-size: 12px;
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid #eee;
        }
    </style>
""", unsafe_allow_html=True)

# --- Header Banner ---
st.markdown("""
    <div class="gov-header">
        <div class="gov-title">Local Government & Policy Navigator</div>
    </div>
""", unsafe_allow_html=True)

# --- Intro ---
st.markdown("### A tool for making public documents readable and relevant.")
st.markdown("Understand city council agendas, school board reports, and policy updates — all in plain language.")

st.markdown("---")

# --- URL Submission ---
st.markdown("### Submit a Public Document", unsafe_allow_html=True)
url = st.text_input("Enter the URL of a government or policy-related webpage")

if url:
    if st.button("Extract and Summarize"):
        with st.spinner("Scraping and summarizing..."):
            main_text = extract_text_from_html(url)
            if main_text.startswith("Error:"):
                st.error(main_text)
            else:
                main_summary = summarize_text_with_bedrock(main_text)
                st.success("Main page summary generated.")
                st.markdown('<div class="section"><h4>Main Page Summary</h4>', unsafe_allow_html=True)
                st.markdown(f"<div class='summary-box'>{main_summary}</div>", unsafe_allow_html=True)

                # Extract and show all internal links
                all_links = extract_links_from_html(url)
                if all_links:
                    st.markdown('<div class="section"><h4>Explore Linked Pages</h4>', unsafe_allow_html=True)

                    # Optional preview
                    st.markdown("Select links below to summarize them. These are all links found on the current page.")

                    # Multiselect UI for user to choose which links to summarize
                    selected_links = st.multiselect(
                        "Choose links to summarize:",
                        options=[link["url"] for link in all_links],
                        format_func=lambda x: next(link["text"] for link in all_links if link["url"] == x)
                    )

                    if selected_links and st.button("Summarize Selected Pages"):
                        for link_url in selected_links:
                            st.markdown(f"#### Summary for [{link_url}]({link_url})", unsafe_allow_html=True)
                            linked_text = extract_text_from_html(link_url)
                            linked_summary = summarize_text_with_bedrock(linked_text)
                            st.markdown(f"<div class='summary-box'>{linked_summary}</div>", unsafe_allow_html=True)
                else:
                    st.warning("No links found on this page.")

# --- Footer ---
st.markdown('<div class="footer">© 2025 LocalGov Navigator. Designed to promote transparency and civic accessibility.</div>', unsafe_allow_html=True)
