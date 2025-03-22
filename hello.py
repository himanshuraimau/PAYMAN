import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PAYMAN_API_KEY = os.getenv("PAYMAN_API_KEY")

# Read Priya's data
try:
    data = pd.read_csv('data.csv')
except FileNotFoundError:
    print("Error: data.csv file not found")
    exit()

def affiliate_performance(data):
    """
    Calculate commissions and performance score for Priya's affiliates.
    Returns ranked DataFrame.
    """
    # Commission: 10% of revenue (configurable later)
    data['commission'] = data['revenue'] * 0.1
    
    # Performance Score: Weighted mix of conversions (30%), revenue (50%), avg_order_value (20%)
    data['performance_score'] = (data['conversions'] * 0.3 + 
                                 data['revenue'] * 0.005 +  # Scaled down due to large revenue values
                                 data['avg_order_value'] * 0.2)
    
    # Rank by performance score
    ranked_data = data.sort_values(by='performance_score', ascending=False)
    return ranked_data

def send_payment(payment_info):
    # Placeholder for your Paymanai logic (simplified for now)
    print(f"Sending ${payment_info['amount']} to {payment_info['name']} via ACH")
    return {"status": "request_sent"}

# Process data
performance = affiliate_performance(data)
print("Affiliate Performance Ranking:")
print(performance[['affiliate_id', 'name', 'conversions', 'revenue', 'avg_order_value', 'commission', 'performance_score']])

# Save the calculated data to a CSV file
output_file = '/home/himanshu/Desktop/payman-play/affiliate_performance.csv'
performance.to_csv(output_file, index=False)
print(f"\nPerformance data saved to {output_file}")

# Automate payouts for top 3 affiliates
print("\nProcessing Payouts:")
for index, row in performance.head(3).iterrows():
    payment_info = {
        "name": row['name'],
        "amount": row['commission'],
        "account_holder_name": row['name'],  # Placeholder, replace with real bank details
        "account_number": "123456789",       # Dummy data
        "routing_number": "987654321",       # Dummy data
        "account_type": "checking",
        "account_holder_type": "individual"
    }
    result = send_payment(payment_info)
    print(f"Payment for {row['name']}: {result}")
