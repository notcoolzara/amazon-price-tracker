# dashboard/app.py

import os
import sys
import subprocess
from datetime import datetime
import importlib.util

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Get root directory
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Method 1: Add to path
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Method 2: Direct import using importlib for config
config_path = os.path.join(ROOT_DIR, "config.py")
spec = importlib.util.spec_from_file_location("config", config_path)
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

# Method 3: Direct import for products_manager
products_manager_path = os.path.join(
    ROOT_DIR, "scraper", "products_manager.py")
spec2 = importlib.util.spec_from_file_location(
    "products_manager", products_manager_path)
products_manager_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(products_manager_module)
ProductsManager = products_manager_module.ProductsManager

CSV_PATH = config.CSV_PATH

st.set_page_config(
    page_title="Amazon Price Tracker Pro",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📊"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF9900;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background-color: #FF9900;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #ec8b00;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize manager
manager = ProductsManager()


def load_data():
    """Load CSV data"""
    if not os.path.isfile(CSV_PATH):
        return pd.DataFrame()
    try:
        df = pd.read_csv(CSV_PATH)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


def calculate_stats(product_df):
    """Calculate price statistics"""
    if product_df.empty or product_df["price"].isna().all():
        return None
    prices = product_df["price"].dropna()
    return {
        "current": prices.iloc[-1] if len(prices) > 0 else None,
        "min": prices.min(),
        "max": prices.max(),
        "avg": prices.mean(),
        "change": prices.iloc[-1] - prices.iloc[0] if len(prices) > 1 else 0,
        "change_pct": ((prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0] * 100) if len(prices) > 1 and prices.iloc[0] > 0 else 0
    }


# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown('<p class="main-header">⚙️ Control Panel</p>',
                unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "➕ Add Product", "📝 Manage Products", "⚙️ Settings"],
        label_visibility="collapsed"
    )

    st.divider()

    # Scrape button
    if st.button("🔄 Scrape All Products", type="primary", width="stretch"):
        with st.spinner("Scraping Amazon... This may take a while..."):
            try:
                result = subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "main.py")],
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=600
                )
                st.success("✅ Scrape completed!")
                st.rerun()
            except subprocess.TimeoutExpired:
                st.error("❌ Scrape timed out (>10 min)")
            except subprocess.CalledProcessError as e:
                st.error(f"❌ Scrape failed")
                with st.expander("Show error details"):
                    st.code(e.stderr if e.stderr else str(e))
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    st.divider()

    # Quick stats
    products = manager.load_products()
    enabled_count = len([p for p in products if p.get("enabled", True)])

    st.metric("Total Products", len(products))
    st.metric("Active Products", enabled_count)

    if os.path.isfile(CSV_PATH):
        file_size = os.path.getsize(CSV_PATH) / 1024
        st.metric("History Size", f"{file_size:.1f} KB")


# ============================================
# PAGE: DASHBOARD
# ============================================
if page == "📊 Dashboard":
    st.markdown('<p class="main-header">📊 Amazon Price Tracker Dashboard</p>',
                unsafe_allow_html=True)

    df = load_data()
    products = manager.load_products()

    if not products:
        st.warning(
            "⚠️ No products tracked yet. Go to 'Add Product' to get started!")
        st.stop()

    # Product selector
    product_options = {
        p["asin"]: f"{p['name']} ({p['asin']})" for p in products}

    selected_asin = st.selectbox(
        "📦 Select Product",
        options=list(product_options.keys()),
        format_func=lambda x: product_options[x]
    )

    product_info = manager.get_product(selected_asin)
    product_df = df[df["asin"] == selected_asin].sort_values("timestamp")

    if product_df.empty:
        st.info("No historical data yet. Click 'Scrape All Products' to fetch data.")
        st.stop()

    # Metrics
    stats = calculate_stats(product_df)
    latest = product_df.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if stats and stats["current"]:
            st.metric(
                "💰 Current Price",
                f"${stats['current']:.2f}",
                delta=f"{stats['change']:+.2f} ({stats['change_pct']:+.1f}%)" if stats["change"] != 0 else None,
                delta_color="inverse"
            )
        else:
            st.metric("💰 Current Price", "N/A")

    with col2:
        target = product_info.get("target_price")
        if target:
            st.metric("🎯 Target Price", f"${target:.2f}")
        else:
            st.metric("🎯 Target Price", "Not Set")

    with col3:
        if stats:
            st.metric("📉 Lowest Price", f"${stats['min']:.2f}")
        else:
            st.metric("📉 Lowest Price", "N/A")

    with col4:
        st.metric("📊 Records", len(product_df))

    st.divider()

    # Price chart
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📈 Price History")

        if not product_df["price"].isna().all():
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=product_df["timestamp"],
                y=product_df["price"],
                mode='lines+markers',
                name='Price',
                line=dict(color='#FF9900', width=3),
                marker=dict(size=8),
                hovertemplate='<b>$%{y:.2f}</b><br>%{x}<extra></extra>'
            ))

            if product_info.get("target_price"):
                fig.add_hline(
                    y=product_info["target_price"],
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Target: ${product_info['target_price']:.2f}"
                )

            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Price ($)",
                hovermode='x unified',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No price data available")

    with col_right:
        st.subheader("📋 Latest Info")

        st.markdown(f"**Product:** {latest['title'][:100]}")
        st.markdown(f"**💵 Price:** {latest['price_raw']}")
        st.markdown(f"**📦 Stock:** {latest['stock']}")
        if pd.notna(latest['rating_raw']):
            st.markdown(f"**⭐ Rating:** {latest['rating_raw']}")
        if pd.notna(latest['reviews_raw']):
            st.markdown(f"**💬 Reviews:** {latest['reviews_raw']}")
        st.markdown(
            f"**🕐 Updated:** {latest['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

        if pd.notna(latest["url"]):
            st.link_button("🔗 View on Amazon",
                           latest["url"], use_container_width=True)

    # Raw data
    with st.expander("📊 View Raw Data"):
        st.dataframe(product_df.tail(
            50), use_container_width=True, hide_index=True)


# ============================================
# PAGE: ADD PRODUCT
# ============================================
elif page == "➕ Add Product":
    st.markdown('<p class="main-header">➕ Add New Product</p>',
                unsafe_allow_html=True)

    with st.form("add_product_form"):
        st.subheader("Product Information")

        col1, col2 = st.columns(2)

        with col1:
            asin = st.text_input(
                "ASIN *", help="Amazon Standard Identification Number (10 characters)")
            name = st.text_input(
                "Product Name *", help="Descriptive name for the product")
            target_price = st.number_input("Target Price ($)", min_value=0.0, step=0.01, value=0.0,
                                           help="Get alerts when price drops below this")

        with col2:
            stock_alert = st.checkbox(
                "Enable Stock Alerts", help="Get notified when item is in stock")

            alert_channels = st.multiselect(
                "Alert Channels",
                ["email", "sms", "telegram", "discord", "slack", "push"],
                default=["email"],
                help="Select notification methods"
            )

        submitted = st.form_submit_button(
            "Add Product", use_container_width=True)

        if submitted:
            if not asin or not name:
                st.error("❌ ASIN and Name are required!")
            elif len(asin) != 10:
                st.error("❌ ASIN must be exactly 10 characters!")
            else:
                price = target_price if target_price > 0 else None
                if manager.add_product(asin, name, price, stock_alert, alert_channels):
                    st.success(f"✅ Added: {name}")
                    st.balloons()
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Product already exists!")

    st.divider()

    # Bulk import
    st.subheader("📁 Bulk Import from CSV")

    st.info("""
    CSV Format: `asin,name,target_price`
    
    Example:
    ```
    B08N5WRWNW,Echo Dot (4th Gen),29.99
    0156007754,Blindness Book,15.00
    ```
    """)

    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded_file:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        count = manager.import_from_csv(tmp_path)
        os.unlink(tmp_path)

        if count > 0:
            st.success(f"✅ Imported {count} products!")
            st.rerun()


# ============================================
# PAGE: MANAGE PRODUCTS
# ============================================
elif page == "📝 Manage Products":
    st.markdown('<p class="main-header">📝 Manage Products</p>',
                unsafe_allow_html=True)

    products = manager.load_products()

    if not products:
        st.info("No products to manage. Add some first!")
        st.stop()

    # Search and filter
    search = st.text_input("🔍 Search products", "")

    filtered = [p for p in products if search.lower(
    ) in p['name'].lower() or search.lower() in p['asin'].lower()]

    st.write(f"Showing {len(filtered)} of {len(products)} products")

    # Product list
    for idx, product in enumerate(filtered):
        with st.expander(f"{'✅' if product.get('enabled', True) else '❌'} {product['name']} ({product['asin']})"):
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.write(f"**ASIN:** {product['asin']}")
                st.write(
                    f"**Target Price:** ${product.get('target_price', 'N/A')}")
                st.write(
                    f"**Stock Alert:** {'Yes' if product.get('stock_alert') else 'No'}")

            with col2:
                st.write(
                    f"**Channels:** {', '.join(product.get('alert_channels', ['email']))}")
                st.write(
                    f"**Status:** {'Enabled' if product.get('enabled', True) else 'Disabled'}")
                st.write(
                    f"**Last Checked:** {product.get('last_checked', 'Never')}")

            with col3:
                if st.button("🔄 Toggle", key=f"toggle_{product['asin']}"):
                    manager.toggle_product(product['asin'])
                    st.rerun()

                if st.button("🗑️ Delete", key=f"delete_{product['asin']}"):
                    manager.delete_product(product['asin'])
                    st.success("Deleted!")
                    st.rerun()

    st.divider()

    # Export
    if st.button("📥 Export All to CSV"):
        export_path = os.path.join(
            ROOT_DIR, "data", f"products_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if manager.export_to_csv(export_path):
            with open(export_path, 'rb') as f:
                st.download_button(
                    "⬇️ Download CSV",
                    f,
                    file_name=os.path.basename(export_path),
                    mime="text/csv"
                )


# ============================================
# PAGE: SETTINGS
# ============================================
elif page == "⚙️ Settings":
    st.markdown('<p class="main-header">⚙️ Settings</p>',
                unsafe_allow_html=True)

    st.subheader("🔔 Alert Configuration")

    st.info("""
    Configure your alert channels directly in `config.py`:
    
    **Example - Enable Email Alerts:**
    ```python
    EMAIL_ENABLED = True
    GMAIL_USERNAME = "your@gmail.com"
    GMAIL_APP_PASSWORD = "your_app_password"
    RECEIVER_EMAIL = "receiver@email.com"
    ```
    
    **Example - Enable Telegram:**
    ```python
    TELEGRAM_ENABLED = True
    TELEGRAM_BOT_TOKEN = "your_bot_token"
    TELEGRAM_CHAT_ID = "your_chat_id"
    ```
    
    **Setup Guides:**
    - **Email**: Get app password from https://myaccount.google.com/apppasswords
    - **SMS**: Sign up at https://www.twilio.com/
    - **Telegram**: Create bot via @BotFather, get chat ID from @userinfobot
    - **Discord**: Server Settings > Integrations > Webhooks
    - **Slack**: https://api.slack.com/messaging/webhooks
    - **Push**: Sign up at https://pushover.net/
    """)

    st.divider()

    st.subheader("📊 Current Status")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Email:**", "✅ Enabled" if config.EMAIL_ENABLED else "❌ Disabled")
        st.write("**SMS:**", "✅ Enabled" if config.SMS_ENABLED else "❌ Disabled")
        st.write("**Telegram:**",
                 "✅ Enabled" if config.TELEGRAM_ENABLED else "❌ Disabled")

    with col2:
        st.write("**Discord:**",
                 "✅ Enabled" if config.DISCORD_ENABLED else "❌ Disabled")
        st.write("**Slack:**", "✅ Enabled" if config.SLACK_ENABLED else "❌ Disabled")
        st.write("**Push:**", "✅ Enabled" if config.PUSH_ENABLED else "❌ Disabled")
