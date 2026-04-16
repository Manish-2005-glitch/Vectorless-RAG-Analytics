import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API = f"{BACKEND_URL}/query"

st.title("📊 AI Data Analyst")

st.caption(f"Backend: {BACKEND_URL}")

q = st.text_input("Ask your question")

if st.button("Run"):
    if not q.strip():
        st.warning("Please enter a question.")
    else:
        try:
            res = requests.post(API, json={"question": q})

            if res.status_code != 200:
                st.error(f"Backend error: {res.status_code}")
                st.text(res.text)
            else:
                res = res.json()

                if "error" in res:
                    st.error(res["error"])
                else:
                    st.subheader("Generated SQL")
                    st.code(res["sql"], language="sql")

                    df = pd.DataFrame(res["result"])

                    st.subheader("Result")
                    st.dataframe(df)

                    if not df.empty:
                        numeric_df = df.select_dtypes(include="number")
                        if not numeric_df.empty:
                            st.subheader("Chart")
                            st.line_chart(numeric_df)

                    st.subheader("Explanation")
                    st.write(res["explanation"])

        except Exception as e:
            st.error(f"Connection error: {e}")