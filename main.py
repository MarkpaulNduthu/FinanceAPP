import json
import os.path

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Finance App", page_icon="<UNK>", layout="wide")

categories_name = "categories.json"
if "categories" not in st.session_state:
    st.session_state["categories"] = {
        "Uncategorized": []
    }
if os.path.exists(categories_name):
    with open(categories_name, "r") as f:
        st.session_state.categories = json.load(f)


def save_categories():
    with open(categories_name, "w") as fp:
        json.dump(st.session_state.categories, fp)


def file_upload(file):
    try:
        df = pd.read_csv(file)
        df.columns = [col.strip() for col in df.columns]
        df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y")
        df['Amount'] = df['Amount'].str.replace(",", "").astype("float64")
        return categorize_transactions(df)
    except Exception as e:
        st.error(f"Error occurred:\n  {e}")
        return None


def categorize_transactions(df):
    df['Category'] = "uncategorized"
    for category, keywords in st.session_state.categories.items():
        if category == "uncategorized" or not keywords:
            continue
        keywords_list = [keyword.strip().lower() for keyword in keywords]
        for indx, row in df.iterrows():
            if row["Details"].lower().strip() in keywords_list:
                df.at[indx, 'Category'] = category
    return df


def save_keyword_to_category(category, keyword):
    st.session_state.categories[category].append(keyword)
    save_categories()


def main():
    st.title("Simple Finance Dashboard")
    uploaded_file = st.file_uploader("Upload CSV File", type="csv")
    if uploaded_file is not None:
        df = file_upload(uploaded_file)
        if df is not None:
            debit_df = df[df["Debit/Credit"] == "Debit"].copy()
            credit_df = df[df["Debit/Credit"] == "Credit"].copy()
            debit_tab, credit_tab = st.tabs(["Debit(s)", "Credit(s)"])
            st.session_state.debit_df = debit_df.copy()
            with debit_tab:
                new_category = st.text_input("Enter New Category").lower().strip().capitalize()
                category_button = st.button("Add Category")
                if category_button and new_category:
                    if new_category not in st.session_state.categories:
                        st.session_state.categories[new_category] = []
                        save_categories()
                        st.rerun()

                debit_tab.subheader("Your Expenses")
                edited_df = st.data_editor(
                    st.session_state.debit_df[['Date', 'Details', 'Amount', 'Category']],
                    column_config={
                        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                        "Amount": st.column_config.NumberColumn(label="Amount", format="%.2f"),
                        "Category": st.column_config.SelectboxColumn(label="Category",
                                                                     options=list(st.session_state.categories.keys())),
                    },
                    use_container_width=True,
                    hide_index=True,
                    key="category_editor"
                )
                save_button = st.button("Apply Changes", type="primary")
                if save_button:
                    for indx, row in edited_df.iterrows():
                        if st.session_state.debit_df.at[indx, 'Category'] == row['Category']:
                            continue
                        save_keyword_to_category(row['Category'], row['Details'])

                st.subheader("Expenses Summary")
                expense_summary_df = st.session_state.debit_df[['Category', 'Amount']].groupby(
                    'Category').sum().reset_index()
                st.dataframe(expense_summary_df,
                             column_config={
                                 "Amount": st.column_config.NumberColumn("Amount", format="%.2f")
                             },
                             hide_index=True,
                             use_container_width=True)
                #     plotting the pie chart
                label = []
                data = []
                for index, row in expense_summary_df.iterrows():
                    label.append(row['Category'])
                    data.append(row['Amount'])
                label = np.array(label)
                data = np.array(data)
                fig, axis = plt.subplots()
                axis.pie(data, autopct='%1.2f%%', radius=0.5, labels=label)
                fig.set_facecolor('none')
                fig.set_figwidth(7)
                axis.legend()
                st.pyplot(fig, use_container_width=False)

            with credit_tab:
                st.subheader("Account Payments")
                amount = credit_df['Amount'].sum()
                st.subheader(f"{amount:,.2f}", divider=True)

                st.write(credit_df)


main()
