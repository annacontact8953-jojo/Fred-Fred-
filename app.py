from datetime import datetime
import io
import pandas as pd
from PIL import Image
import streamlit as st

# ==================== CONFIGURATION ====================
ACCESS_PASSWORD = "25062506"

# 🌟 固定的使用者與個人專屬 PIN / 密碼（永久保存）
DEFAULT_USERS = {
    "Default User": "Freddypoo",
    "Jo": "2410",
    "Fred": "2506",
}
# ========================================================

st.set_page_config(
    page_title="ATO Expense Tracker", page_icon="🧾", layout="centered"
)

# Language Dictionary
TEXTS = {
    "English": {
        "title": "🧾 ATO Tax Expense Tracker",
        "subtitle": (
            "Track work-related expenses & Super contributions with personal"
            " user PINs."
        ),
        "pwd_title": "🔒 Access Required",
        "pwd_desc": (
            "Please enter main password to access the tax deduction tracker."
        ),
        "pwd_label": "Main Password",
        "login_btn": "Login",
        "pwd_err": "❌ Incorrect password",
        "tab1": "📝 Quick Entry",
        "tab2": "📋 View Records",
        "user_select": "Select User / Friend",
        "user_pin_label": "Enter User PIN / Password",
        "user_login_btn": "🔓 User Login",
        "pin_error": "❌ Incorrect user PIN. Please try again.",
        "login_success_msg": "🎉 Successfully logged in as:",
        "logout_btn": "Switch User / Logout",
        "current_user_banner": "✏️ Currently logging expenses for:",
        "upload_label": "1. Upload Receipt (Optional)",
        "receipt_loaded": "Receipt uploaded!",
        "date_label": "2. Date",
        "cat_label": "3. Category",
        "desc_label": "4. Description / Item",
        "desc_ph": "e.g., Fuel, Personal Super Contribution, Course",
        "amount_label": "5. Amount (AUD)",
        "save_btn": "✅ Save Expense",
        "empty_desc_warn": "Please provide a description!",
        "save_success": "🎉 Expense saved successfully!",
        "records_title": "📋 Tax Deductions Records",
        "total_amount": "Total Claimable Amount",
        "download_excel": "📥 Download Excel File for Tax Return",
        "no_records": "No expenses recorded yet.",
        "sidebar_title": "📊 Live Summary",
        "sidebar_total": "Total:",
        "cats": {
            "🚗 Car & Travel": "Work-related car expenses",
            "📚 Self-Education": "Self-education expenses",
            "👕 Uniform & Gear": "Work-related clothing, uniform",
            "🏦 Personal Super Contributions": (
                "Personal superannuation contributions"
            ),
            "💼 Other Work Expenses": "Other work-related expenses",
        },
    },
    "繁體中文": {
        "title": "🧾 澳洲報稅隨手記帳",
        "subtitle": "支援多使用者與個人專屬小密碼（PIN），輕鬆記錄工作開支與 Super。",
        "pwd_title": "🔒 請輸入系統總密碼",
        "pwd_desc": "本工具含有私人財務紀錄，請輸入總密碼解鎖。",
        "pwd_label": "總密碼",
        "login_btn": "登入",
        "pwd_err": "❌ 總密碼錯誤，請重新輸入",
        "tab1": "📝 快速記帳",
        "tab2": "📋 查看所有紀錄",
        "user_select": "選擇使用者 / 朋友",
        "user_pin_label": "請輸入該使用者的專屬密碼 (PIN)",
        "user_login_btn": "🔓 登入使用者",
        "pin_error": "❌ 使用者密碼錯誤，請重新輸入！",
        "login_success_msg": "🎉 成功登入為：",
        "logout_btn": "切換使用者 / 登出",
        "current_user_banner": "✏️ 目前正在為以下使用者記帳：",
        "upload_label": "1. 拍照或上傳收據（選填）",
        "receipt_loaded": "收據已上傳！",
        "date_label": "2. 消費日期",
        "cat_label": "3. 支出類別",
        "desc_label": "4. 項目說明",
        "desc_ph": "例如: 加油、個人退休金提撥 (Super)、買書",
        "amount_label": "5. 金額 (AUD)",
        "save_btn": "✅ 儲存紀錄",
        "empty_desc_warn": "請填寫項目說明！",
        "save_success": "🎉 紀錄成功儲存！",
        "records_title": "📋 目前累積的扣除額紀錄",
        "total_amount": "目前總扣除金額",
        "download_excel": "📥 下載報稅用 Excel 檔案",
        "no_records": "目前還沒有任何紀錄，快去新增第一筆吧！",
        "sidebar_title": "📊 即時總覽報表",
        "sidebar_total": "總計金額：",
        "cats": {
            "🚗 工作車資 (Car & Travel)": "Work-related car expenses",
            "📚 進修教育 (Self-Education)": "Self-education expenses",
            "👕 工作制服 (Uniform & Equipment)": "Work-related clothing, uniform",
            "🏦 個人退休金自願提撥 (Super)": (
                "Personal superannuation contributions"
            ),
            "💼 Other Work Expenses": "Other work-related expenses",
        },
    },
}

# Sidebar Language Selection
lang = st.sidebar.selectbox("🌐 Language / 語言", ["English", "繁體中文"])
t = TEXTS[lang]

# Main Password Check Logic
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

if not st.session_state.password_correct:
    st.title(t["pwd_title"])
    st.markdown(t["pwd_desc"])
    entered_pwd = st.text_input(t["pwd_label"], type="password")
    if st.button(t["login_btn"]):
        if entered_pwd == ACCESS_PASSWORD:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error(t["pwd_err"])
    st.stop()

# Initialize State Data
if "user_data" not in st.session_state:
    st.session_state.user_data = pd.DataFrame(
        columns=[
            "User",
            "Date",
            "Category",
            "Description",
            "Amount (AUD)",
            "Note",
        ]
    )

if "users_dict" not in st.session_state:
    st.session_state.users_dict = DEFAULT_USERS

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# ==================== SIDEBAR LIVE SUMMARY ====================
st.sidebar.markdown("---")
st.sidebar.subheader(t["sidebar_title"])
df_sidebar = st.session_state.user_data
if not df_sidebar.empty:
    total_all = df_sidebar["Amount (AUD)"].sum()
    st.sidebar.metric(label=t["sidebar_total"], value=f"${total_all:,.2f} AUD")

    st.sidebar.markdown("**By User / 依使用者統計:**")
    user_summary = (
        df_sidebar.groupby("User")["Amount (AUD)"].sum().reset_index()
    )
    for _, row in user_summary.iterrows():
        st.sidebar.text(f"• {row['User']}: ${row['Amount (AUD)']:,.2f}")
else:
    st.sidebar.info(
        "No data yet / 尚無資料"
        if lang == "English"
        else "尚無記帳資料"
    )

# ==================== MAIN APP ====================
st.title(t["title"])
st.markdown(t["subtitle"])

tab1, tab2 = st.tabs([t["tab1"], t["tab2"]])

with tab1:
    user_list = list(st.session_state.users_dict.keys())
    selected_user = st.selectbox(t["user_select"], user_list)

    if st.session_state.get("prev_selected_user") != selected_user:
        st.session_state.logged_in_user = None
        st.session_state.prev_selected_user = selected_user

    if st.session_state.logged_in_user == selected_user:
        st.success(f"{t['login_success_msg']} **{selected_user}**")
        if st.button(t["logout_btn"]):
            st.session_state.logged_in_user = None
            st.rerun()

        st.markdown(f"### {t['current_user_banner']} `{selected_user}`")

        with st.form("expense_form", clear_on_submit=True):
            receipt_file = st.file_uploader(
                t["upload_label"], type=["jpg", "jpeg", "png"]
            )

            if receipt_file is not None:
                image = Image.open(receipt_file)
                st.image(
                    image,
                    caption=t["receipt_loaded"],
                    use_container_width=True,
                )

            date = st.date_input(t["date_label"], value=datetime.today())
            display_category = st.selectbox(
                t["cat_label"], list(t["cats"].keys())
            )
            description = st.text_input(
                t["desc_label"], placeholder=t["desc_ph"]
            )
            amount = st.number_input(
                t["amount_label"], min_value=0.0, step=1.0, value=0.0
            )

            submitted = st.form_submit_button(t["save_btn"])

            if submitted:
                if not description.strip():
                    st.warning(t["empty_desc_warn"])
                else:
                    new_entry = {
                        "User": selected_user,
                        "Date": str(date),
                        "Category": t["cats"][display_category],
                        "Description": description,
                        "Amount (AUD)": amount,
                        "Note": (
                            "Receipt Attached"
                            if receipt_file is not None
                            else "Manual Entry"
                        ),
                    }
                    st.session_state.user_data = pd.concat(
                        [
                            st.session_state.user_data,
                            pd.DataFrame([new_entry]),
                        ],
                        ignore_index=True,
                    )
                    st.success(t["save_success"])
                    st.rerun()

    else:
        entered_user_pin = st.text_input(t["user_pin_label"], type="password")
        if st.button(t["user_login_btn"]):
            correct_pin = st.session_state.users_dict.get(selected_user, "")
            if entered_user_pin == correct_pin:
                st.session_state.logged_in_user = selected_user
                st.rerun()
            else:
                st.error(t["pin_error"])

with tab2:
    st.subheader(t["records_title"])
    df = st.session_state.user_data

    if not df.empty:
        total = df["Amount (AUD)"].sum()
        st.metric(label=t["total_amount"], value=f"${total:,.2f} AUD")
        st.dataframe(df, use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Tax_Deductions")
        excel_data = output.getvalue()

        st.download_button(
            label=t["download_excel"],
            data=excel_data,
            file_name=f"Tax_Deductions_{datetime.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info(t["no_records"])