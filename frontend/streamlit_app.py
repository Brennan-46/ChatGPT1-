import streamlit as st
import requests

st.title("Business Agent UI")
api_url = st.text_input("API URL", "http://localhost:8000/v1/agent/run")
user_id = st.text_input("User ID", "demo-user")
prompt = st.text_area("Prompt", "Schedule a 30-minute meeting tomorrow")

if st.button("Run Agent"):
    res = requests.post(api_url, json={"user_id": user_id, "prompt": prompt}, timeout=30)
    st.json(res.json())
