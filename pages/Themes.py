import streamlit as st
import json
import os


def init():
    if "db" not in os.listdir("../"):
        os.mkdir("../db")
    if "themes.json" not in os.listdir("../db"):
        file = open("../db/themes.json", "w")
        theme = {
            "dark": {
                "bg": "black",
                "bg2": "#5591f5",
                "pr": "#c98bdb",
                "text": "white"
            },
            "light": {
                "bg": "white",
                "bg2": "#82E1D7",
                "pr": "#5591f5",
                "text": "black"
            },
            "custom": {
                "bg": "#bbbabb",
                "bg2": "#a29595",
                "pr": "#c3a07d",
                "text": "#000000"
            }
        }
        json.dump(theme, file, indent=4)
        file.close()
    if "themes" not in st.session_state.keys():
        st.session_state["themes"] = json.load(open("../db/themes.json", "r"))


def check_different(elem1, elem2):
    min = elem1 if len(elem1) < len(elem2) else elem2
    other = elem2 if min == elem1 else elem1
    for i, elem in enumerate(list(min)):
        if elem != list(other)[i]:
            return True
    return False


def theme_io():
    theme_json = st.file_uploader("load a theme JSON")

    cols = st.columns([4, 2, 4])
    with cols[0]:
        if st.button("import"):
            if theme_json is not None:
                theme["custom"] = json.load(theme_json)
                st.success("imported!")
            else:
                st.error("please upload a theme file first.")
    with cols[2]:
        st.download_button(
            label="Export",
            data=json.dumps(st.session_state["themes"]["custom"], indent=4),
            file_name='theme.json',
            mime='application/json',
        )


def custom_theme(theme):
    new_theme = st.session_state["themes"]["custom"].copy()
    new_theme["bg"] = st.color_picker("background", theme["custom"]["bg"])
    new_theme["bg2"] = st.color_picker("background secondary", theme["custom"]["bg2"])
    new_theme["pr"] = st.color_picker("primary", theme["custom"]["pr"])
    new_theme["text"] = st.color_picker("text color", theme["custom"]["text"])
    cols = st.columns([3, 1])
    with cols[0]:
        theme_name = st.text_input("Theme name")
        if st.button("save custom theme"):
            if len(theme_name) > 0:
                st.session_state["themes"].update({theme_name: new_theme})
                json.dump(st.session_state["themes"], open("../db/themes.json", "w"), indent=4)
                st.rerun()
            else:
                st.error("please enter a valid theme name!")

    with cols[1]:
        st.write("Preview:")
        st.button("Primary", type="primary")
        st.button("Secondary", type="secondary")

    return new_theme


def theme_selection():
    theme = st.session_state["themes"].copy()
    options = st.session_state["themes"].keys()
    columns = st.columns([2, 1])
    with columns[1]:
        theme_io()  # import export

    with columns[0]:
        st.selectbox("theme", options=options, key="themebutton")
        selected_theme = st.session_state["themebutton"]

        placeholder = st.empty()

        new_theme = st.session_state["themes"]["custom"].copy()
        if selected_theme == "custom":
            new_theme = custom_theme(theme)  # custom themes

        is_changed = check_different(new_theme.items(), st.session_state["themes"]["custom"].items())

        if is_changed:
            theme["custom"] = new_theme
            st.session_state["themes"]["custom"] = new_theme

        set_btn = False
        if selected_theme != "custom":
            set_btn = placeholder.button("set")

        if (set_btn) or is_changed:
            st._config.set_option(f'theme.base', "dark")
            st._config.set_option(f'theme.backgroundColor', theme[selected_theme]["bg"])
            st._config.set_option(f'theme.secondaryBackgroundColor', theme[selected_theme]["bg2"])
            st._config.set_option(f'theme.primaryColor', theme[selected_theme]["pr"])
            st._config.set_option(f'theme.textColor', theme[selected_theme]["text"])

            st.rerun()


def main():
    init()
    theme_selection()


if __name__ == '__main__':
    main()