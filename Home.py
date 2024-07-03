'''
title: Home
'''
import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
import numpy as np
from local_components import card_container
from streamlit_shadcn_ui import slider, input, textarea, radio_group, switch

# with open("docs/introduction.md", "r") as f:
#     st.markdown(f.read())

# ui.date_picker()
st.set_page_config(page_title='Home', page_icon='C3_Only_Ball.png', layout='wide')
banner_path = 'Horizontal_Banner_NoSC.png'
st.image(banner_path, width=400)
st.header("C3 Toolbase")
ui.badges(badge_list=[ ("Under Construction", "destructive")], class_name="flex gap-2", key="main_badges1")
st.caption("A  component library for any tools drafted, under development, or finalized for C3 Nonprofit Consulting.")



with ui.element("div", className="flex gap-2", key="buttons_group1"):
    ui.element("link_button", text="C3 Homepage", url="https://c3nonprofitconsulting.com/?utm_term=nonprofit%20consulting&utm_campaign=C3-+Brand+Awareness&utm_source=adwords&utm_medium=ppc&hsa_acc=8247911146&hsa_cam=20228363163&hsa_grp=151208392713&hsa_ad=660673815301&hsa_src=g&hsa_tgt=kwd-14670921&hsa_kw=nonprofit%20consulting&hsa_mt=b&hsa_net=adwords&hsa_ver=3&gad_source=1&gclid=Cj0KCQjwiYOxBhC5ARIsAIvdH52NrutsioWsNxpB825rl2yFsqVYmaxjCjkBK5YmWGnrv0Ke6V0hqjcaAhH0EALw_wcB", variant="outline", key="btn2")

st.subheader("Notes")

st.write("4.18.2024: Demo of 990 Search Tool")
st.write("4.23.2024: Added Living Wage Dashboard")
st.write("4.23.2024: Created Updated & Unupdated versions of 990 Search Tool")
st.write("4.24.2024: Site unblocked by IT")
st.write("4.25.2024: Added a submit comment/question page")
