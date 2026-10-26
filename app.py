from datetime import datetime
import io
import re
import pandas as pd
from PIL import Image, ImageEnhance
import streamlit as st

# Optional local OCR using pytesseract if installed on deployment
try:
    import pytesseract

    HAS_OCR = True
except ImportError:
    HAS_OCR = False

# ==================== CONFIGURATION ====================
ACCESS_PASSWORD = "25062506"
# ========================================================

st.set_page_config(
    page_title="ATO Expense Tracker", page_icon="🧾", layout="centered"
)

# Language Dictionary
TEXTS = {
    "English": {
        "title": "🧾 ATO Tax Expense Tracker",
        "subtitle": "Track work-related expenses quickly for Australian tax deductions.",
        "pwd_title": "🔒 Access Required",
        "pwd_desc": "Please enter password to access the tax deduction tracker.",
        "pwd_label": "Password",
        "login_btn": "Login",
        "pwd_err": "❌ Incorrect password",
        "tab1": "📝 Quick Entry",
        "tab2": "📋 View Records",
        "upload_label": "1. Upload Receipt (Auto-Extracts Info)",
        "receipt_loaded": "Receipt uploaded!",
        "auto_detected": "✨ Auto-detected info from receipt! (Please review)",
        "date_label": "2. Date",
        "cat_label": "3. Category",
        "desc_label": "4. Description / Item",
        "desc_ph": "e.g., Fuel, Office Supplies, Training Course",
        "amount_label": "5. Amount (AUD)",
        "save_btn": "✅ Save Expense",
        "empty_desc_warn": "Please provide a description!",
        "save_success": "🎉 Expense saved successfully!",
        "records_title": "📋 Total Tax Deductions",
        "total_amount": "Total Claimable Amount",
        "download_excel": "📥 Download Excel File for Tax Return",
        "no_records": "No expenses recorded yet.",
        "cats": {
            "🚗 Car & Travel": "Work-related car expenses",
            "📚 Self-Education": "Self-education expenses",
            "👕 Uniform & Gear": "Work-related clothing, uniform",
            "💼 Other Work Expenses": "Other work-related expenses",
        },
    },
    "繁體中文": {
        "title": "🧾 澳洲報稅隨手記帳",
        "subtitle": "拍照自動帶入資訊，快速整理 ATO 扣除額。",
        "pwd_title": "🔒 請輸入存取密碼",
        "pwd_desc": "本工具含有私人財務紀錄，請輸入密碼解鎖。",
        "pwd_label": "密碼",
        "login_btn": "登入",
        "pwd_err": "❌ 密碼錯誤，請重新輸入",
        "tab1": "📝 快速記帳",
        "tab2": "📋 查看所有紀錄",
        "upload_label": "1. 拍照或上傳收據（自動辨識資訊）",
        "receipt_loaded": "收據已上傳！",
        "auto_detected": "✨ 已自動從收據擷取資料！（請核對是否準確）",
        "date_label": "2. 消費日期",
        "cat_label": "3. 支出類別",
        "desc_label": "4. 項目說明",
        "desc_ph": "例如: 加油、辦公用品、課程費用",
        "amount_label": "5. 金額 (AUD)",
        "save_btn": "✅ 儲存紀錄",
        "empty_desc_warn": "請填寫項目說明！",
        "save_success": "🎉 紀錄成功儲存！",
        "records_title": "📋 目前累積的扣除額紀錄",
        "total_amount": "目前總扣除金額",
        "download_excel": "📥 下載報稅用 Excel 檔案",
        "no_records": "目前還沒有任何紀錄，快去新增第一筆吧！",
        "cats": {
            "🚗 工作車資 (Car & Travel)": "Work-related car expenses",
            "📚 進修教育 (Self-Education)": "Self-education expenses",
            "👕 工作制服 (Uniform & Equipment)": "Work-related clothing, uniform",
            "💼 其他工作開支 (Other Expenses)": "Other work-related expenses",
        },
    },
}

# Sidebar Language Selection
lang = st.sidebar.selectbox("🌐 Language / 語言", ["English", "繁體中文"])
t = TEXTS[lang]


# OCR Helper Function
def parse_receipt_text(text):
    data = {}
    # Extract Amount (looks for $XX.XX or total XX.XX)
    amounts = re.findall(r"\$?\s*(\d+\.\d{2})", text)
    if amounts:
        try:
            data["amount"] = float(amounts[-1])  # Usually total is near the bottom
        except ValueError:
            pass

    # Extract Date (matches YYYY-MM-DD or DD/MM/YYYY)
    date_match = re.search(r"(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})", text)
    if date_match:
        raw_date = date_match.group(1)
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                data["date"] = datetime.strptime(raw_date, fmt).date()
                break
            except ValueError:
                pass
    return data


# Password Check Logic
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

# Initialize Expense Data
if "user_data" not in st.session_state:
    st.session_state.user_data = pd.DataFrame(
        columns=["Date", "Category", "Description", "Amount (AUD)", "Note"]
    )

st.title(t["title"])
st.markdown(t["subtitle"])

tab1, tab2 = st.tabs([t["tab1"], t["tab2"]])

with tab1:
    receipt_file = st.file_uploader(
        t["upload_label"], type=["jpg", "jpeg", "png"]
    )

    detected_date = datetime.today()
    detected_amount = 0.0
    detected_desc = ""

    if receipt_file is not None:
        image = Image.open(receipt_file)
        st.image(image, caption=t["receipt_loaded"], use_container_width=True)

        if HAS_OCR:
            try:
                # Basic OCR processing
                text = pytesseract.image_to_string(image)
                extracted = parse_receipt_text(text)
                if "amount" in extracted:
                    detected_amount = extracted["amount"]
                if "date" in extracted:
                    detected_date = extracted["date"]
                st.info(t["auto_detected"])
            except Exception:
                pass

    with st.form("expense_form", clear_on_submit=True):
        date = st.date_input(t["date_label"], value=detected_date)
        display_category = st.selectbox(t["cat_label"], list(t["cats"].keys()))
        description = st.text_input(
            t["desc_label"],
            value=detected_desc,
            placeholder=t["desc_ph"],
        )
        amount = st.number_input(
            t["amount_label"],
            value=float(detected_amount),
            min_value=0.0,
            step=1.0,
        )

        submitted = st.form_submit_button(t["save_btn"])

        if submitted:
            if not description.strip():
                st.warning(t["empty_desc_warn"])
            else:
                new_entry = {
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