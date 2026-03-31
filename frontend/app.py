import os
from datetime import date, timedelta

import altair as alt
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Listen AI Dashboard", layout="wide")

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")

if "token" not in st.session_state:
    st.session_state.token = None

st.title("ListenAI Dashboard")
st.caption("Track sentiment, keywords, trends, and example posts by keyword filters.")
st.text("Hello! 張千瑜")

dashboard_tab, add_post_tab = st.tabs(["Dashboard", "Add Post"])

with st.sidebar:
    st.subheader("Authentication")
    username = st.text_input("Username", value="admin")
    password = st.text_input("Password", type="password", value="admin123")

    if st.button("Login", use_container_width=True):
        try:
            resp = requests.post(
                f"{GATEWAY_URL}/auth/login",
                json={"username": username, "password": password},
                timeout=10,
            )
            if resp.status_code == 200:
                st.session_state.token = resp.json().get("token")
                st.success("Login successful")
            else:
                st.error(resp.json().get("error", "Login failed"))

        except Exception as exc:
            st.error(f"Gateway error: {exc}")

    if st.session_state.token:
        st.success("Authenticated")

with dashboard_tab:
    col1, col2 = st.columns(2)
    with col1:
        include_input = st.text_input("Include keywords (comma-separated)", "機器人")
    with col2:
        exclude_input = st.text_input("Exclude keywords (comma-separated)", "")

    range_col1, range_col2, range_col3 = st.columns([2, 2, 1])
    with range_col1:
        from_date = st.date_input("From date", value=date.today() - timedelta(days=365))
    with range_col2:
        to_date = st.date_input("To date", value=date.today() + timedelta(days=365))
    with range_col3:
        sample_size = st.number_input("Example posts", min_value=1, max_value=20, value=5)

    run_clicked = st.button("Analyze", type="primary")

    if run_clicked:
        if not st.session_state.token:
            st.warning("Please login first.")
        else:
            include_keywords = [k.strip() for k in include_input.split(",") if k.strip()]
            exclude_keywords = [k.strip() for k in exclude_input.split(",") if k.strip()]

            payload = {
                "includeKeywords": include_keywords,
                "excludeKeywords": exclude_keywords,
                "fromDate": from_date.strftime("%Y-%m-%d"),
                "toDate": to_date.strftime("%Y-%m-%d"),
                "sampleSize": int(sample_size),
            }

            try:
                with st.spinner("Building dashboard..."):
                    resp = requests.post(
                        f"{GATEWAY_URL}/api/dashboard",
                        json=payload,
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                        timeout=30,
                    )

                if resp.status_code != 200:
                    st.error(resp.json().get("error", "Request failed"))
                    st.stop()

                data = resp.json()
                sentiment = data.get("sentimentPercentage", {})

                st.metric("Mentions", data.get("mentionCount", 0))

                st.subheader("Sentiment")
                sentiment_df = pd.DataFrame(
                    [
                        {"sentiment": "positive", "value": sentiment.get("positive", 0)},
                        {"sentiment": "neutral", "value": sentiment.get("neutral", 0)},
                        {"sentiment": "negative", "value": sentiment.get("negative", 0)},
                    ]
                )

                sentiment_chart = (
                    alt.Chart(sentiment_df)
                    .mark_arc()
                    .encode(
                        theta=alt.Theta(field="value", type="quantitative"),
                        color=alt.Color(
                            "sentiment:N",
                            scale=alt.Scale(
                                domain=["positive", "neutral", "negative"],
                                range=["#2e7d32", "#9e9e9e", "#c62828"],
                            ),
                            legend=alt.Legend(title="Sentiment"),
                        ),
                        tooltip=["sentiment:N", alt.Tooltip("value:Q", title="Percentage")],
                    )
                    .properties(height=320)
                )
                st.altair_chart(sentiment_chart, use_container_width=True)

                st.subheader("Top Keywords")
                top_keywords = data.get("topKeywords", [])
                if top_keywords:
                    kw_df = pd.DataFrame(top_keywords)
                    if {"keyword", "count"}.issubset(kw_df.columns):
                        kw_df = kw_df[kw_df["count"] > 0].copy()
                        kw_df = kw_df.sort_values("count", ascending=False)
                        if not kw_df.empty:
                            kw_chart = (
                                alt.Chart(kw_df)
                                .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
                                .encode(
                                    x=alt.X("count:Q", title="Mentions"),
                                    y=alt.Y("keyword:N", sort="-x", title="Keyword"),
                                    tooltip=[
                                        alt.Tooltip("keyword:N", title="Keyword"),
                                        alt.Tooltip("count:Q", title="Mentions"),
                                    ],
                                    color=alt.ColorValue("#2e7d32"),
                                )
                                .properties(height=420)
                            )
                            st.altair_chart(kw_chart, use_container_width=True)
                        else:
                            st.info("No keyword frequencies available for chart.")
                    else:
                        st.info("Keyword data is missing expected fields.")
                else:
                    st.info("No keywords found for this filter.")

                st.subheader("Post Trend")
                trends = data.get("trends", [])
                if trends:
                    trends_df = pd.DataFrame(trends)
                    chart = (
                        alt.Chart(trends_df)
                        .mark_line(point=True)
                        .encode(x="date:T", y="count:Q")
                        .properties(height=300)
                    )
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No trend data found.")

                st.subheader("Example Posts")
                examples = data.get("examplePosts", [])
                if not examples:
                    st.info("No posts found for your keyword filters.")
                for post in examples:
                    content = (post.get("content", "") or "").replace("\\n", "\n")
                    st.markdown(
                        f"**[{post.get('platform', 'unknown')}] @{post.get('author', 'user')}** "
                        f"({post.get('created_at', '')})  \n"
                        f"Sentiment: **{post.get('sentiment', 'neutral')}**  \n"
                        f"{content}"
                    )
                    st.divider()

            except Exception as exc:
                st.error(f"Error: {exc}")

with add_post_tab:
    st.subheader("Add Post Manually")
    st.caption("Insert a post into the database so it can appear in dashboard analysis.")

    with st.form("manual_post_form"):
        platform_input = st.text_input("Platform", value="x")
        author_input = st.text_input("Author", value="manual_user")
        created_at_input = st.text_input("Created at (RFC3339, optional)", value="")
        content_input = st.text_area("Content", height=160)
        submit_post = st.form_submit_button("Insert Post", type="primary")

    if submit_post:
        if not st.session_state.token:
            st.warning("Please login first.")
        else:
            payload = {
                "platform": platform_input,
                "author": author_input,
                "content": content_input,
                "createdAt": created_at_input,
            }
            try:
                resp = requests.post(
                    f"{GATEWAY_URL}/api/posts",
                    json=payload,
                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                    timeout=20,
                )
                if resp.status_code == 201:
                    post_id = resp.json().get("id")
                    st.success(f"Post inserted successfully (id: {post_id}).")
                else:
                    try:
                        err_data = resp.json()
                    except ValueError:
                        err_data = {"error": "request failed", "detail": resp.text}
                    st.error(f"Insert failed: {err_data.get('error', 'request failed')}")
                    if err_data.get("detail"):
                        st.error(f"Detail: {err_data['detail']}")
            except Exception as exc:
                st.error(f"Gateway error: {exc}")
