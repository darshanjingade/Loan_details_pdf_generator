import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# Loan details
principal = 2200000
emi = 26000
interest_rate = 0.074 / 12
loan_period_months = 10 * 12
preclosure_amount = 100000
with_pre_closure = 'B'# 'Y-yes', 'N-no', 'B-both'
logo_path = "dj_logo.png"  # your logo file path

# Create amortization schedules with early payoff logic
def create_amortization_schedule(prepay=False):
    data = {
        'Month': [],
        'EMI': [],
        'Principal Paid': [],
        'Interest Paid': [],
        'Remaining Principal': [],
        'Prepayment': [],
    }

    remaining = principal
    month = 1
    while month <= loan_period_months and remaining > 0:
        interest = remaining * interest_rate
        # Calculate EMI or last payment adjustment
        total_due = remaining + interest
        if total_due <= emi:
            emi_actual = total_due
            principal_part = remaining
            interest_part = emi_actual - principal_part
            remaining = 0
        else:
            emi_actual = emi
            interest_part = interest
            principal_part = emi_actual - interest_part
            remaining -= principal_part

        prepayment = 0
        if prepay and month % 12 == 0 and remaining > 0:
            prepay_amount = min(preclosure_amount, remaining)
            remaining -= prepay_amount
            prepayment = prepay_amount

        data['Month'].append(month)
        data['EMI'].append(round(emi_actual, 2))
        data['Principal Paid'].append(round(principal_part, 2))
        data['Interest Paid'].append(round(interest_part, 2))
        data['Remaining Principal'].append(round(remaining if remaining > 0 else 0, 2))
        data['Prepayment'].append(round(prepayment, 2))

        if remaining <= 0:
            break
        month += 1

    return pd.DataFrame(data)

df_without = create_amortization_schedule(prepay=False)
df_with = create_amortization_schedule(prepay=True)

# PDF generation
def generate_pdf(df_without, df_with='', filename="amortization_schedule.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    row_height = 15
    column_widths = [60, 70, 90, 90, 110, 80]
    headers = list(df_without.columns)

    def draw_loan_details():
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, height - 50, "Loan Details:")

        c.setFont("Helvetica", 10)
        c.drawString(40, height - 70, f"Principal Amount: {principal:,.2f}Rs")
        c.drawString(40, height - 90, f"Monthly EMI: {emi:,.2f}Rs")
        c.drawString(40, height - 110, f"Interest Rate (Annual): {interest_rate * 12 * 100:.2f}%")
        c.drawString(40, height - 130, f"Loan Period: {loan_period_months // 12} years ({loan_period_months} months)")
        if with_pre_closure in ['Y','B']:
            c.drawString(40, height - 150, f"Preclosure Amount per year end: {preclosure_amount:,.2f}Rs")
        c.line(40, height - 160, width - 40, height - 160)

        # Add logo on top-right corner of loan details box
        logo_width = 100
        logo_height = 50

        x = width - logo_width - 40
        y = height - 50 - logo_height / 2  # Align vertically with "Loan Details" title

        try:
            c.drawImage(logo_path, x, y, width=logo_width, height=logo_height, preserveAspectRatio=True)
        except Exception as e:
            print(f"Logo not found or error drawing logo: {e}")

    def draw_table(df, title, start_page=True):
        rows = df.values.tolist()
        headers = list(df.columns)
        column_widths = [60, 70, 90, 90, 110, 80]
        row_height = 15
        year_marker_extra_height = 20  # Extra vertical space for year-end line + label

        total_rows = len(rows)
        global_row_index = 0
        page = 0

        while global_row_index < total_rows:
            c.setFont("Helvetica", 10)
            page += 1

            if page == 1 and start_page:
                draw_loan_details()
                y = height - 180
                max_rows = int((height - 180 - 40) / row_height)
            else:
                y = height - 50
                max_rows = int((height - 50 - 40) / row_height)

            # Table title (only on first page of this table)
            if page == 1:
                c.setFont("Helvetica-Bold", 12)
                c.drawString(40, y, title)
                c.setFont("Helvetica", 10)
                y -= row_height

            # Draw header
            for j, header in enumerate(headers):
                c.drawString(45 + sum(column_widths[:j]), y, str(header))
            y -= row_height

            rows_on_this_page = 0
            while rows_on_this_page < max_rows and global_row_index < total_rows:
                row = rows[global_row_index]
                current_month = row[0]

                # Check if the current row is end of year (12, 24, ...)
                is_year_end = (current_month % 12 == 0)

                # Calculate required space after drawing the row
                needed_space = row_height
                if is_year_end:
                    needed_space += year_marker_extra_height

                # Check if there is enough space to draw this row + marker
                if y - needed_space < 40:
                    break  # Not enough space, move to next page

                # Draw the row data
                for j, cell in enumerate(row):
                    # Format numbers with ₹ symbol and commas for all except Month
                    if j == 0:
                        c.drawString(45 + sum(column_widths[:j]), y, str(cell))
                    else:
                        c.drawRightString(45 + sum(column_widths[:j]) + column_widths[j] - 5, y, f"{cell:,.2f}Rs")
                y -= row_height  # move down after the row

                # Draw year-end line and label with enough padding
                if is_year_end:
                    # Draw a horizontal line below the row with some padding
                    line_y = y - 5
                    c.setStrokeColor(colors.lightgrey)
                    c.line(40, line_y, width - 40, line_y)
                    c.setStrokeColor(colors.black)

                    # Draw year label below the line
                    year_num = current_month // 12
                    c.setFont("Helvetica-Oblique", 9)
                    label_y = line_y - 12  # some padding below the line
                    c.drawString(45, label_y, f"End of Year {year_num}")
                    c.setFont("Helvetica", 10)

                    y = label_y - 10  # move y down to avoid overlap with next row

                global_row_index += 1
                rows_on_this_page += 1

            if global_row_index < total_rows:
                c.showPage()

    if with_pre_closure == 'B':
        # Draw both tables
        draw_table(df_without, "Amortization Schedule", start_page=True)
        c.showPage()
        draw_table(df_with, "Amortization Schedule With Prepayment", start_page=False)
    elif with_pre_closure == 'Y':
        draw_table(df_with, "Amortization Schedule With Prepayment", start_page=True)
    else:
        draw_table(df_without, "Amortization Schedule", start_page=True)

    c.save()

# Generate the PDF
generate_pdf(df_without, df_with)

