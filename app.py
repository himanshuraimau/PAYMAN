import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from hello import affiliate_performance, send_payment

# Check for visualization dependencies
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    visualization_available = True
except ImportError:
    visualization_available = False
    st.warning("""
    Visualization libraries are not installed. To enable charts, please run:
    ```
    pip install matplotlib seaborn
    ```
    Then restart the app.
    """)

# Page configuration
st.set_page_config(page_title="Affiliate Performance Dashboard", layout="wide")
st.title("Affiliate Performance Dashboard")

# Load environment variables
load_dotenv()

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Payments", "Settings"])

# Read data
@st.cache_data
def load_data():
    try:
        data = pd.read_csv('data.csv')
        try:
            payment_data = pd.read_csv('payment_data.csv')
        except FileNotFoundError:
            payment_data = None
            st.warning("Payment data file not found, some features will be limited.")
        return data, payment_data
    except FileNotFoundError as e:
        st.error(f"Error loading data: {e}")
        return None, None

data, payment_data = load_data()

if data is not None:
    if page == "Dashboard":
        # Calculate performance metrics
        performance_data = affiliate_performance(data)
        
        # Display metrics in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Affiliates", len(performance_data))
        with col2:
            st.metric("Total Revenue", f"${performance_data['revenue'].sum():,.2f}")
        with col3:
            st.metric("Total Commission", f"${performance_data['commission'].sum():,.2f}")
        
        # Performance Table
        st.subheader("Affiliate Performance Ranking")
        st.dataframe(performance_data[['affiliate_id', 'name', 'conversions', 'revenue', 
                                       'avg_order_value', 'commission', 'performance_score']], 
                    use_container_width=True)
        
        # Visualizations - only if libraries are available
        if visualization_available:
            st.subheader("Visualizations")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Performance Score Distribution
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(x='name', y='performance_score', data=performance_data.head(10), ax=ax)
                ax.set_title('Top 10 Affiliates by Performance Score')
                ax.set_xlabel('Affiliate')
                ax.set_ylabel('Performance Score')
                plt.xticks(rotation=45)
                st.pyplot(fig)
            
            with col2:
                # Revenue vs Commission
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.scatterplot(x='revenue', y='commission', size='conversions', 
                               hue='performance_score', data=performance_data, ax=ax)
                ax.set_title('Revenue vs Commission')
                ax.set_xlabel('Revenue ($)')
                ax.set_ylabel('Commission ($)')
                st.pyplot(fig)
        else:
            st.info("Install matplotlib and seaborn to view performance visualizations")
        
        # Download the performance data as CSV
        st.download_button(
            label="Download Performance Data as CSV",
            data=performance_data.to_csv(index=False).encode('utf-8'),
            file_name='affiliate_performance.csv',
            mime='text/csv',
        )
        
    elif page == "Payments":
        st.subheader("Process Payments")
        
        if payment_data is not None:
            # Calculate performance to get commission data
            performance_data = affiliate_performance(data)
            
            # Merge performance data with payment data
            payment_info = pd.DataFrame()
            payment_info['name'] = performance_data['name']
            payment_info['affiliate_id'] = performance_data['affiliate_id']
            payment_info['commission'] = performance_data['commission'].round(2)
            
            # Display payment information
            st.dataframe(payment_info, use_container_width=True)
            
            # Allow user to select affiliates for payment
            selected_affiliates = st.multiselect(
                "Select Affiliates for Payment",
                options=payment_info['name'].tolist(),
                default=payment_info['name'].head(3).tolist()
            )
            
            if st.button("Process Selected Payments"):
                if selected_affiliates:
                    for affiliate in selected_affiliates:
                        affiliate_info = performance_data[performance_data['name'] == affiliate].iloc[0]
                        
                        # For a real app, you would fetch the banking details from payment_data
                        payment_details = {
                            "name": affiliate_info['name'],
                            "amount": affiliate_info['commission'],
                            "account_holder_name": affiliate_info['name'],
                            "account_number": "123456789",  # Dummy data
                            "routing_number": "987654321",  # Dummy data
                            "account_type": "checking",
                            "account_holder_type": "individual"
                        }
                        
                        result = send_payment(payment_details)
                        st.success(f"Payment processed for {affiliate}: {result}")
                else:
                    st.warning("Please select at least one affiliate for payment")
                    
            # Bulk payment option
            st.subheader("Bulk Payments")
            if st.button("Pay Top 3 Performers"):
                top_affiliates = performance_data.head(3)
                for _, affiliate in top_affiliates.iterrows():
                    payment_details = {
                        "name": affiliate['name'],
                        "amount": affiliate['commission'],
                        "account_holder_name": affiliate['name'],
                        "account_number": "123456789",  # Dummy data
                        "routing_number": "987654321",  # Dummy data
                        "account_type": "checking",
                        "account_holder_type": "individual"
                    }
                    result = send_payment(payment_details)
                    st.success(f"Payment processed for {affiliate['name']}: {result}")
        else:
            st.warning("Payment data not available")
    
    elif page == "Settings":
        st.subheader("Application Settings")
        
        # Commission settings
        st.write("Commission Settings")
        commission_rate = st.slider("Default Commission Rate (%)", 1, 30, 10)
        
        # Performance score weights
        st.write("Performance Score Weights")
        conversion_weight = st.slider("Conversion Weight", 0.0, 1.0, 0.3)
        revenue_weight = st.slider("Revenue Weight", 0.0, 0.01, 0.005)
        aov_weight = st.slider("Average Order Value Weight", 0.0, 1.0, 0.2)
        
        if st.button("Save Settings"):
            # In a real app, you would save these settings to a config file or database
            st.success("Settings saved successfully!")
            
        # Data management
        st.subheader("Data Management")
        
        uploaded_file = st.file_uploader("Upload new affiliate data (CSV)", type="csv")
        if uploaded_file is not None:
            # In a real app, you would process and validate the uploaded file
            st.success("File uploaded successfully! Data will be processed.")
            
else:
    st.error("Failed to load data. Please check the data files and try again.")
    
    # Provide example data format
    st.info("""
    The app expects a data.csv file with these columns:
    - affiliate_id
    - name
    - conversions
    - revenue
    - avg_order_value
    
    Example:
    ```
    affiliate_id,name,conversions,revenue,avg_order_value
    1,GreenBlog,50,5000,100
    2,EcoInfluencer,30,3000,100
    ```
    """)
