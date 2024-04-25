import streamlit as st
import pandas as pd
from datetime import datetime

# Path to the Excel file
excel_file_path = 'comments.xlsx'

# Load or initialize the comments DataFrame
try:
    # Try to load the existing comments
    comments_df = pd.read_excel(excel_file_path)
except FileNotFoundError:
    # Initialize an empty DataFrame and save it if not found
    comments_df = pd.DataFrame(columns=['ID', 'Timestamp', 'Name', 'Comment', 'Reply'])

# Function to save DataFrame to Excel
def save_comments():
    comments_df.to_excel(excel_file_path, index=False)

# Form for new comments
with st.form('comment_form'):
    name = st.text_input("Name:")
    comment = st.text_area("Leave a comment or question:")
    submit_comment = st.form_submit_button('Submit Comment')

if submit_comment and comment:
    new_id = len(comments_df) + 1 if not comments_df.empty else 1
    new_comment = pd.DataFrame({
        'ID': [new_id],
        'Timestamp': [datetime.now()],
        'Name': [name],
        'Comment': [comment],
        'Reply': ['']
    })
    comments_df = pd.concat([comments_df, new_comment], ignore_index=True)
    save_comments()

st.write("## Comments and Replies")

# Choose a comment to reply to
comment_to_reply = st.selectbox('Select a comment to reply to:', 
                                options=[f"{row['Name']}: {row['Comment'][:50]}... (ID: {row['ID']})" for _, row in comments_df.iterrows()],
                                format_func=lambda x: x.split(" (ID:")[0])

# Extract the ID of the selected comment
selected_id = int(comment_to_reply.split(" (ID: ")[-1][:-1])

# Reply form
with st.form(key='reply_form'):
    reply = st.text_area("Write your reply:")
    submit_reply = st.form_submit_button('Submit Reply')

if submit_reply and reply:
    # Find the index of the comment
    comment_index = comments_df.index[comments_df['ID'] == selected_id].tolist()[0]
    comments_df.at[comment_index, 'Reply'] = reply
    save_comments()

# Display the comments and replies
for _, row in comments_df.iterrows():
    st.text(f"{row['Name']}: {row['Comment']}")
    if row['Reply']:
        st.text(f"Reply: {row['Reply']}")
