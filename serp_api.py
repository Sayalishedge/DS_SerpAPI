import json
import streamlit as st
import serpapi  # Use direct client import
from openai import OpenAI
import tomllib
import os

# --- CONFIGURATION & CLIENT SETUP ---
with open("secrets.toml", "rb") as f:
    secrets = tomllib.load(f)
    # Accessing the data
    OPENAI_KEY = secrets["openai"]["api_key"]
    SERPAPI_KEY = secrets["serpapi"]["api_key"]

client = OpenAI(api_key=OPENAI_KEY)

st.set_page_config(page_title="HCP Affiliation Finder", layout="wide")

def get_affiliations(name):
    # 1. Search Google via SerpApi
    st.info(f"Searching Google for: {name}...")
    
    try:
        # Use the official Client initialization
        search_client = serpapi.Client(api_key=SERPAPI_KEY)
        
        # Pull direct organic results
        results = search_client.search({
            "engine": "google",
            "q": f"{name} healthcare physician hospital affiliation",
            "num": 10
        })
        organic_results = results.get("organic_results", [])
    except Exception as e:
        st.error(f"Error fetching search results: {e}")
        return None

    if not organic_results:
        return None

    # Create context for the AI
    context = ""
    for i, res in enumerate(organic_results):
        context += f"Source {i+1}: {res.get('title')} - {res.get('snippet')}\n\n"

    # 2. Parse with OpenAI
    st.info("AI is extracting affiliations...")
    prompt = f"""
    Based on these search results for the doctor {name}, identify the top 5 hospital or clinical affiliations.
    Return ONLY a JSON object with a key 'affiliations' containing a list of objects.
    Each object must have: 'Organization_Name', 'Location', and 'Source_Link'.

    Search Data:
    {context}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a medical data analyst."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Load and return the JSON content safely
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error processing with OpenAI: {e}")
        return None

# --- UI LAYOUT ---
st.title("🏥 HCP Affiliation Search")
target_hcp = st.text_input("Enter HCP Name:", value="William Pilcher")

if st.button("Find Affiliations"):
    if not target_hcp.strip():
        st.warning("Please enter a valid HCP name.")
    else:
        try:
            data = get_affiliations(target_hcp)
            
            if data and "affiliations" in data and data["affiliations"]:
                affiliations = data["affiliations"]
                st.success(f"Found {len(affiliations)} affiliations for {target_hcp}")
                
                # Using st.dataframe for an interactive grid
                st.dataframe(affiliations, use_container_width=True)
            else:
                st.warning("No clear affiliations found in the search snippets.")
                
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")