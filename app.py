import streamlit as st
import gspread

from google.oauth2.service_account import Credentials
from datetime import datetime


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Sachitha's Sales",
    page_icon="🍗",
    layout="centered"
)


# =========================================================
# PRODUCTS AND PRICES
# =========================================================

PRODUCTS = {
    "Roll Shawarma": 60,
    "Plate Shawarma": 110,
    "Meat Shawarma roll": 80,
    "Meat Shawarma Plate": 140,
    "Tikka": 70,
    "Boneless Tikka": 240,
    "Quarter Alfam": 150,
    "Half Alfam": 240,
    "Full Alfam": 420,
}
# =========================================================
# SESSION STATE
# =========================================================

if "cart" not in st.session_state:
    st.session_state.cart = {
        item: 0
        for item in PRODUCTS
    }

if "form_version" not in st.session_state:
    st.session_state.form_version = 0

if "save_message" not in st.session_state:
    st.session_state.save_message = None


# =========================================================
# SHOW SAVE MESSAGE
# =========================================================

if st.session_state.save_message:
    st.success(st.session_state.save_message)
    st.session_state.save_message = None


# =========================================================
# GOOGLE SHEETS CONNECTION
# =========================================================

@st.cache_resource
def connect_to_google_sheet():

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=scopes
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open(
        st.secrets["google_sheet_name"]
    )

    worksheet = spreadsheet.worksheet("Sales")

    return worksheet


# Connect to Google Sheet
worksheet = connect_to_google_sheet()


# =========================================================
# SETUP GOOGLE SHEET
# =========================================================

def setup_sheet():

    headers = [
        "Sale ID",
        "Date",
        "Time",
        "Item",
        "Quantity",
        "Unit Price",
        "Total",
        "Payment Method",
    ]

    existing_headers = worksheet.row_values(1)

    if existing_headers != headers:

        worksheet.update(
            "A1:H1",
            [headers]
        )


# =========================================================
# ADD SALE
# =========================================================

def add_sale(items, payment):

    sale_id = datetime.now().strftime(
        "%Y%m%d%H%M%S%f"
    )

    now = datetime.now()

    total = 0

    rows = []

    for item, quantity in items.items():

        amount = PRODUCTS[item] * quantity

        total += amount

        rows.append([
            sale_id,
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            item,
            quantity,
            PRODUCTS[item],
            amount,
            payment,
        ])

    worksheet.append_rows(
        rows,
        value_input_option="USER_ENTERED"
    )

    return total, sale_id


# =========================================================
# GET TODAY'S SUMMARY
# =========================================================

def today_summary():

    records = worksheet.get_all_records()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    sales = 0
    cash = 0
    upi = 0
    items = 0

    orders = set()

    for row in records:

        if str(row.get("Date", "")) != today:
            continue

        sale_id = row.get("Sale ID")

        total = float(
            row.get("Total") or 0
        )

        quantity = int(
            row.get("Quantity") or 0
        )

        payment = row.get(
            "Payment Method"
        )

        orders.add(sale_id)

        sales += total

        items += quantity

        if payment == "Cash":
            cash += total

        elif payment == "UPI":
            upi += total

    return (
        sales,
        cash,
        upi,
        items,
        len(orders)
    )


# =========================================================
# TODAY'S ITEM SALES
# =========================================================

def today_item_sales():

    records = worksheet.get_all_records()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    quantities = {
        item: 0
        for item in PRODUCTS
    }

    amounts = {
        item: 0
        for item in PRODUCTS
    }

    for row in records:

        if str(row.get("Date", "")) != today:
            continue

        item = row.get("Item")

        if item not in PRODUCTS:
            continue

        quantity = int(
            row.get("Quantity") or 0
        )

        amount = float(
            row.get("Total") or 0
        )

        quantities[item] += quantity

        amounts[item] += amount

    return quantities, amounts


# =========================================================
# INITIALIZE SHEET
# =========================================================

setup_sheet()


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 700px;
        padding: 1rem .8rem 2rem;
    }

    h1 {
        text-align: center;
    }

    div.stButton > button {
        min-height: 48px;
        border-radius: 12px;
        font-weight: 700;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# TITLE
# =========================================================

st.title("🍗 Sachitha's Sales")

st.caption(
    "Quick shop billing & daily sales tracking"
)


# =========================================================
# TODAY'S SUMMARY
# =========================================================

sales, cash, upi, item_count, orders = (
    today_summary()
)


c1, c2 = st.columns(2)

c1.metric(
    "Today's Sales",
    f"₹{sales:,.0f}"
)

c2.metric(
    "Orders",
    orders
)


c3, c4 = st.columns(2)

c3.metric(
    "Items Sold",
    item_count
)

c4.metric(
    "Cash + UPI",
    f"₹{cash + upi:,.0f}"
)


# =========================================================
# NEW SALE
# =========================================================

st.divider()

st.subheader("🧾 New Sale")


if "cart" not in st.session_state:

    st.session_state.cart = {
        item: 0
        for item in PRODUCTS
    }
    if "form_version" not in st.session_state:
        st.session_state.form_version = 0


# =========================================================
# PRODUCT LIST
# =========================================================

for item, price in PRODUCTS.items():

    a, b, c = st.columns(
        [2.7, 1.1, 1.2]
    )

    a.markdown(
        f"**{item}**"
    )

    a.caption(
        f"₹{price} each"
    )

    quantity = b.number_input(
        "Qty",
        min_value=0,
        max_value=99,
        value=0,
        step=1,
        key=f"qty_{item}_{st.session_state.form_version}",
        label_visibility="collapsed"
    )

    st.session_state.cart[item] = quantity

    c.markdown(
        f"""
        <div style="
            padding-top:8px;
            text-align:right;
            font-weight:700;
        ">
        ₹{price * quantity:,}
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# SELECTED ITEMS
# =========================================================

selected = {
    item: quantity
    for item, quantity
    in st.session_state.cart.items()
    if quantity > 0
}


total = sum(
    PRODUCTS[item] * quantity
    for item, quantity in selected.items()
)


items = sum(
    selected.values()
)


# =========================================================
# TOTAL
# =========================================================

st.divider()

st.markdown(
    f"## Total: ₹{total:,}"
)

st.caption(
    f"{items} item(s) selected"
)


# =========================================================
# PAYMENT METHOD
# =========================================================

payment = st.radio(
    "Payment Method",
    ["Cash", "UPI"],
    horizontal=True
)


# =========================================================
# SAVE SALE
# =========================================================

if st.button(
    "✅ SAVE SALE",
    type="primary",
    use_container_width=True
):
    if not selected:
        st.warning("Please select at least one item.")
    else:
        amount, sale_id = add_sale(selected, payment)

        # Clear all selected quantities
        for item in PRODUCTS:
            st.session_state.cart[item] = 0

        # Show confirmation
        st.success(f"Saved ₹{amount:,.0f} — {payment}")

        # Refresh the Streamlit page
        st.rerun()


# =========================================================
# CLEAR SELECTION
# =========================================================

if st.button(
    "🗑️ Clear Selection",
    use_container_width=True
):

    st.session_state.cart = {
        item: 0
        for item in PRODUCTS
    }
    st.session_state.form_version += 1

    st.rerun()


# =========================================================
# TODAY'S ITEM SALES
# =========================================================

st.divider()

st.subheader(
    "📊 Today's Item Sales"
)


quantities, amounts = (
    today_item_sales()
)


for item in PRODUCTS:

    if quantities[item] > 0:

        st.write(
            f"**{item}** — "
            f"{quantities[item]} sold — "
            f"₹{amounts[item]:,.0f}"
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "☁️ Sales are stored in your online Google Sheet."
)
