import pandas as pd

# Loan details
principal = 2200000  # Initial principal
emi = 26000  # Monthly EMI
interest_rate = 0.074 / 12  # Monthly interest rate (7.4% annual rate)
loan_period_months = 10 * 12  # 10 years in months
preclosure_amount = 100000


# Create lists to store the table data
months = []
emi_values = []
principal_paid = []
interest_paid = []
remaining_principal = []
prepayment = []

# Scenario 1: Without Prepayment
remaining_principal_without_prepayment = principal
for month in range(1, loan_period_months + 1):
    interest_payment = remaining_principal_without_prepayment * interest_rate
    principal_payment = emi - interest_payment
    remaining_principal_without_prepayment -= principal_payment

    months.append(month)
    emi_values.append(emi)
    principal_paid.append(principal_payment)
    interest_paid.append(interest_payment)
    remaining_principal.append(int(remaining_principal_without_prepayment))
    prepayment.append(0)

# Scenario 2: With Prepayment (every year ₹1,00,000 paid)
remaining_principal_with_prepayment = principal
for month in range(1, loan_period_months + 1):
    interest_payment = remaining_principal_with_prepayment * interest_rate
    principal_payment = emi - interest_payment
    remaining_principal_with_prepayment -= principal_payment

    # Add prepayment at the end of each year (12th, 24th, etc. month)
    if month % 12 == 0:
        remaining_principal_with_prepayment -= preclosure_amount
        prepayment_amount = preclosure_amount
    else:
        prepayment_amount = 0

    months.append(month)
    emi_values.append(emi)
    principal_paid.append(principal_payment)
    interest_paid.append(interest_payment)
    remaining_principal.append(int(remaining_principal_with_prepayment))
    prepayment.append(prepayment_amount)

# Combine the results into two separate dataframes
df_without_prepayment = pd.DataFrame({
    'Month': months[:loan_period_months],
    'EMI': emi_values[:loan_period_months],
    'Principal Paid': principal_paid[:loan_period_months],
    'Interest Paid': interest_paid[:loan_period_months],
    'Remaining Principal': remaining_principal[:loan_period_months],
    'Prepayment': prepayment[:loan_period_months]
})

df_with_prepayment = pd.DataFrame({
    'Month': months[loan_period_months:],
    'EMI': emi_values[loan_period_months:],
    'Principal Paid': principal_paid[loan_period_months:],
    'Interest Paid': interest_paid[loan_period_months:],
    'Remaining Principal': remaining_principal[loan_period_months:],
    'Prepayment': prepayment[loan_period_months:]
})

# # Display the first few rows of each table
# print("Without Prepayment (First Few Months):")
# print(df_without_prepayment.head())

# print("\nWith Prepayment (First Few Months):")
# print(df_with_prepayment.head())

# Output the entire amortization schedule for both scenarios
print("Amortization Schedule Without Prepayment (for 10 years):")
print(df_without_prepayment)

print("\nAmortization Schedule With Prepayment (for 10 years):")
print(df_with_prepayment)