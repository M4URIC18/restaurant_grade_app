# pages/3_Blog.py

import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(page_title="Blog – CleanKitchen NYC", layout="wide")

st.title("📝 CleanKitchen NYC Blog")
st.subheader("Project Updates, Experiments, and Fixes")

st.write("This blog tracks progress, insights, and improvements made while building CleanKitchen NYC.")

st.divider()

# ============================================
# Load blog posts from JSON
# ============================================
BLOG_PATH = os.path.join("data", "blog_posts.json")

if not os.path.exists(BLOG_PATH):
    st.error("❌ blog_posts.json not found in /data folder.")
    st.stop()

with open(BLOG_PATH, "r") as f:
    posts = json.load(f)

# ============================================
# Collect all tags
# ============================================
all_tags = sorted({tag for post in posts for tag in post["tags"]})

selected_tags = st.multiselect(
    "Filter by tags",
    options=all_tags,
    default=[],
    help="Use this filter to show only posts matching certain topics."
)

def post_matches_tags(post):
    if not selected_tags:
        return True
    return any(tag in post["tags"] for tag in selected_tags)

# Sort posts (newest first)
posts_sorted = sorted(posts, key=lambda x: x["date"], reverse=True)

# ============================================
# Render blog posts
# ============================================
for post in posts_sorted:
    if not post_matches_tags(post):
        continue

    with st.container():
        st.markdown(f"### **{post['title']}**")

        # Format date
        dt = datetime.strptime(post["date"], "%Y-%m-%d")
        st.caption(f"📅 {dt.strftime('%b %d, %Y')}")

        # Tags
        tag_badges = " ".join(
            [f"<span style='background:#eee;padding:4px 8px;border-radius:8px;margin-right:6px;font-size:13px;'>{tag}</span>"
             for tag in post["tags"]]
        )
        st.markdown(tag_badges, unsafe_allow_html=True)

        st.write("")  # spacing

        # Optional image
        if post.get("image"):
            img_path = post["image"]
            if os.path.exists(img_path):
                st.image(img_path, use_container_width=True)
            else:
                st.warning(f"Image not found: {img_path}")

        # Content list
        for bullet in post["content"]:
            st.write(f"- {bullet}")

        st.markdown("---")

# Footer
st.info("More posts coming soon!")
