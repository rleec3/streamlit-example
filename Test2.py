

css = 
[data-testid="stVerticalBlock"].red [data-testid="stText"] {
    color: red;
}
[data-testid="stVerticalBlock"].big [data-testid="stText"] {
    font-size: 2em;
}
[data-testid="stVerticalBlock"].flex {
    flex-direction: row !important;
}
[data-testid="stVerticalBlock"].flex > div {
    flex: 0 0 1.75rem !important;
}
[data-testid="stVerticalBlock"].rainbow {
    padding: 0.5em;
    border: 4px solid;
    border-image-slice: 1;
    border-image-source: linear-gradient(to bottom right, #b827fc 0%, #2c90fc 25%, #b8fd33 50%, #fec837 75%, #fd1892 100%);
}
[data-testid="stVerticalBlock"].icon button {
    font: var(--fa-font-solid);
    width: 2.5em;
}
[data-testid="stVerticalBlock"].save_icon {
    color: #2c90fc;
}
[data-testid="stVerticalBlock"].rainbow_button button {
    border-top-color: #b827fc;
    border-left-color: #2c90fc;
    border-bottom-color: #b8fd33;
    border-right-color: #fec837;
}
[data-testid="stVerticalBlock"].save_icon button::before {
    display: inline-block;
    text-rendering: auto;
    font: var(--fa-font-regular);
    content: "\\f0c7";
    margin-right: 0.25em;
}


st.markdown(
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css" />',
    unsafe_allow_html=True,
)

st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

with st.container():
    st.text("hello")

with st.container(css_classes=["big", "red", "rainbow"]):
    st.text("world")

with st.container(css_classes=["flex"]):
    with st.container(css_classes=["icon"]):
        st.button("\uf6d5")

    with st.container(css_classes=["icon"]):
        st.button("\uf6e2")

    with st.container(css_classes=["icon"]):
        st.button("\uf810")

    with st.container(css_classes=["icon", "rainbow_button"]):
        st.button("\uf4fb")

with st.container(css_classes=["save_icon", "rainbow_button"]):
    st.button("Save")