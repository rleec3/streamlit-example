import streamlit as st
import pandas as pd
from datetime import datetime



#Title
st.set_page_config(page_title='Submit A  Comment', page_icon='C3_Only_Ball.png', layout='wide')
banner_path = 'Horizontal_Banner_NoSC.png'
st.image(banner_path, width=400)
st.header("Submit A Comment")

# Constants for status categories
STATUS_OPTIONS = {
    "Solved": "✅",
    "In Progress": "🚧",
    "Not Reviewed": "❔"
}

# Path to the Excel file
excel_file_path = 'comments.xlsx'

# Load or initialize the comments DataFrame
try:
    comments_df = pd.read_excel(excel_file_path)
except FileNotFoundError:
    comments_df = pd.DataFrame(columns=['ID', 'Timestamp', 'Name', 'Comment', 'Replies', 'Upvotes', 'Status'])

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
            'Timestamp': datetime.now().date(),  # Use datetime.date() to ensure we only get the date
            'Name': name,
            'Comment': comment,
            'Replies': '',
            'Upvotes': 0,
            'Status': STATUS_OPTIONS['Not Reviewed']
        }
        comments_df = comments_df.append(new_comment, ignore_index=True)
        save_comments(comments_df)

with col2:  # Column for replying to an existing comment
    if not comments_df.empty:
        comment_to_reply_id = st.selectbox('Select a comment to reply to:', comments_df['ID'])
        with st.form('reply_form'):
            reply_name = st.text_input("Your name (for reply):")
            reply_text = st.text_area("Write your reply:")
            submit_reply = st.form_submit_button('Submit Reply')
        if submit_reply and reply_text and reply_name:
            comment_index = comments_df.index[comments_df['ID'] == comment_to_reply_id].tolist()[0]
            new_reply = f"{reply_name}: {reply_text}\n"
            comments_df.at[comment_index, 'Replies'] = (comments_df.at[comment_index, 'Replies'] or '') + new_reply
            save_comments(comments_df)

# Layout for changing status of comments
with st.form('status_form'):
    col1, col2 = st.columns(2)
    with col1:
        comment_to_change_status_id = st.selectbox('Select a comment to change status:', comments_df['ID'], key='status_id')
    with col2:
        status_to_change = st.selectbox("Change Status", list(STATUS_OPTIONS.keys()), key='status_select')
        submit_status = st.form_submit_button('Update Status')
    if submit_status:
        comment_index = comments_df.index[comments_df['ID'] == comment_to_change_status_id].tolist()[0]
        comments_df.at[comment_index, 'Status'] = STATUS_OPTIONS[status_to_change]
        save_comments(comments_df)

# Display the comments and replies
st.write("## Comments and Replies")
for index, row in comments_df.iterrows():
    cols = st.columns([3, 2])
    with cols[0]:  # Display comment info, upvotes and delete button
        formatted_date = pd.to_datetime(row['Timestamp']).strftime('%Y-%m-%d') if pd.notnull(row['Timestamp']) else "Date not available"
        st.markdown(f"**Comment ID {row['ID']} by {row['Name']}**")
        st.write(f"Date: {formatted_date}")
        st.write(f"Comment: *{row['Comment']}*")
        st.write(f"Status: {row['Status']}")
        upvote_button, delete_button = st.columns([1, 1])
        with upvote_button:
            if st.button('👍 Upvote', key=f"upvote_{index}"):
                comments_df.at[index, 'Upvotes'] += 1
                save_comments(comments_df)
            st.write(f"Upvotes: {row['Upvotes']}")
        with delete_button:
            if st.button('Delete', key=f"delete_{index}"):
                comments_df = comments_df.drop(index)
                comments_df.reset_index(drop=True, inplace=True)
                save_comments(comments_df)
    with cols[1]:  # Display replies
        st.write("**Replies:**")
        # Check if 'Replies' is not NaN before attempting to split
        if not pd.isna(row['Replies']) and row['Replies'].strip():
            for reply in row['Replies'].split('\n'):
                if reply:  # Ensure there's something to print
                    st.write(reply)
        else:
            st.write("*No replies yet.*")
