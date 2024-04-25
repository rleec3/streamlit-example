import streamlit as st
import pandas as pd
from datetime import datetime



#Title
banner_path = 'Horizontal_Banner_NoSC.png'
st.image(banner_path, width=400)
st.title("Submit A Comment")


# Path to the Excel file
excel_file_path = 'comments.xlsx'

# Define constants for status categories
STATUS_OPTIONS = {
    "Solved": "✅",
    "In Progress": "🚧",
    "Not Reviewed": "❔"
}

# Load or initialize the comments DataFrame
try:
    comments_df = pd.read_excel(excel_file_path)
except FileNotFoundError:
    comments_df = pd.DataFrame(columns=['ID', 'Timestamp', 'Name', 'Comment', 'Reply', 'Upvotes', 'Status'])

# Function to save DataFrame to Excel
def save_comments(df):
    df.to_excel(excel_file_path, index=False)

# Layout for adding new comments and replying to existing ones
col1, col2 = st.columns(2)

with col1:  # Column for adding a new comment
    with st.form('comment_form'):
        name = st.text_input("Name:")
        comment = st.text_area("Leave a comment or question:")
        submit_comment = st.form_submit_button('Submit Comment')
    if submit_comment and comment:
        new_id = len(comments_df) + 1 if not comments_df.empty else 1
        new_comment = {
            'ID': new_id,
            'Timestamp': datetime.now(),
            'Name': name,
            'Comment': comment,
            'Reply': '',
            'Upvotes': 0,
            'Status': STATUS_OPTIONS['Not Reviewed']  # Use the emoji for 'Not Reviewed'
        }
        comments_df = pd.concat([comments_df, pd.DataFrame([new_comment])], ignore_index=True)
        save_comments(comments_df)

with col2:  # Column for replying to an existing comment
    if not comments_df.empty:
        comment_to_reply_id = st.selectbox('Select a comment to reply to:', comments_df['ID'])
        with st.form('reply_form'):
            reply = st.text_area("Write your reply:")
            submit_reply = st.form_submit_button('Submit Reply')
        if submit_reply and reply:
            comment_index = comments_df.index[comments_df['ID'] == comment_to_reply_id].tolist()[0]
            comments_df.at[comment_index, 'Reply'] = reply
            save_comments(comments_df)

# Section to display comments, replies, upvotes, and status
st.write("## Comments and Replies")
for index, row in comments_df.iterrows():
    st.write(f"Comment ID {row['ID']} by {row['Name']} on {row['Timestamp']}")
    st.write(f"\"{row['Comment']}\"")
    col1, col2, col3, col4 = st.columns([1, 4, 1, 1])  # Add another column for delete button
    with col1:
        if st.button('👍 Upvote', key=f"upvote_{index}"):
            comments_df.at[index, 'Upvotes'] = row.get('Upvotes', 0) + 1
            save_comments(comments_df)
        st.write(f"Upvotes: {row.get('Upvotes', 0)}")
    with col2:
        # Handle status change with the correct list and indices
        current_status_index = list(STATUS_OPTIONS.values()).index(row['Status'])
        new_status = st.selectbox("Change Status", list(STATUS_OPTIONS.keys()), index=current_status_index, key=f"status_{index}")
        if STATUS_OPTIONS[new_status] != row['Status']:
            comments_df.at[index, 'Status'] = STATUS_OPTIONS[new_status]
            save_comments(comments_df)
    with col3:
        if st.button('Delete', key=f"delete_{index}"):
            comments_df = comments_df.drop(index)
            comments_df.reset_index(drop=True, inplace=True)
            save_comments(comments_df)
    st.write(f"Reply: {row['Reply']}")
