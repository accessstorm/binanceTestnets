import streamlit as st
from decimal import Decimal
from bot.orders import place_order
from bot.client import get_client  # Fixed import name
from bot.validators import validate_order_inputs

# Configure the page
st.set_page_config(page_title="Testnet Trading Bot", page_icon="📈", layout="centered")

st.title("📈 Binance Futures Testnet Bot")
st.markdown("A lightweight UI for placing USDT-M futures orders.")
st.markdown("---")

# Create a clean form for user inputs
with st.form("order_form"):
    st.subheader("Order Details")
    
    symbol = st.text_input("Symbol", value="BTCUSDT").upper()
    
    col1, col2 = st.columns(2)
    with col1:
        side = st.selectbox("Side", options=["BUY", "SELL"])
    with col2:
        order_type = st.selectbox("Order Type", options=["MARKET", "LIMIT"])
    
    quantity = st.number_input("Quantity", min_value=0.001, step=0.001, format="%.3f")
    
    # Show price input only if LIMIT is selected (logic handles the display)
    price = st.number_input("Price (Required for LIMIT)", min_value=0.0, step=0.1, format="%.2f")
    
    # The submit button
    submit_button = st.form_submit_button(label="Place Order on Testnet")

# Handle the button click
if submit_button:
    try:
        # 1. Run our strict validators
        validated_params = validate_order_inputs(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price if order_type == "LIMIT" else None
        )
        
        with st.spinner("Connecting to Binance Testnet..."):
            # 2. Initialize the correct client function
            client = get_client()
            
            # 3. Place the order
            response = place_order(
                client=client,
                symbol=validated_params["symbol"],
                side=validated_params["side"],
                order_type=validated_params["order_type"],
                quantity=validated_params["quantity"],
                price=validated_params["price"]
            )
            
            st.success("✅ Order placed successfully!")
            
            # Display important fields back to the user
            st.json({
                "Order ID": response.get("orderId"),
                "Status": response.get("status"),
                "Avg Price": response.get("avgPrice"),
                "Executed Qty": response.get("executedQty")
            })
            
    except ValueError as ve:
        # Catch our custom validation errors
        st.error(f"⚠️ Validation Error: {str(ve)}")
    except Exception as e:
        # Catch API or network errors
        st.error(f"❌ Failed to place order: {str(e)}")
