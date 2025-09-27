import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import logging

# -----------------------------
# Configurations (Parameters)
# -----------------------------

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Loan Parameters
principal = 2200000
emi = 26000
interest_rate = 0.074 / 12
loan_period_months = 10 * 12
preclosure_amount = 100000
prepayment_interval = 12
with_pre_closure = 'B'  # 'Y', 'N', 'B'

# PDF & Layout Parameters
logo_path = "dj_logo.png"
page_margin_left = 40
page_margin_right = 40
row_height = 15
column_widths = [60, 70, 90, 90, 110, 80]

# Company Information (to display under the logo)
company_name = "Dream Junction Finance Pvt. Ltd."
company_address = "123, Business Park, MG Road, Bengaluru - 560001"
company_email = "contact@dreamjunction.in"
company_phone = "+91-98765-43210"


# -----------------------------
# Amortization Schedule Logic
# -----------------------------

def create_amortization_schedule(principal, emi, interest_rate, loan_period_months, preclosure_amount=None, prepayment_interval=12, prepay=False):
    data = {
        'Month': [], 'EMI': [], 'Principal Paid': [], 'Interest Paid': [],
        'Remaining Principal': [], 'Prepayment': [],
    }
    remaining = principal
    month = 1
    while month <= loan_period_months and remaining > 0:
        interest = remaining * interest_rate
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
        if prepay and month % prepayment_interval == 0 and remaining > 0:
            prepay_amount = min(preclosure_amount, remaining)
            remaining -= prepay_amount
            prepayment = prepay_amount

        data['Month'].append(month)
        data['EMI'].append(round(emi_actual, 2))
        data['Principal Paid'].append(round(principal_part, 2))
        data['Interest Paid'].append(round(interest_part, 2))
        data['Remaining Principal'].append(round(max(remaining, 0), 2))
        data['Prepayment'].append(round(prepayment, 2))

        if remaining <= 0:
            break
        month += 1

    return pd.DataFrame(data)

# -----------------------------
# PDF Generation
# -----------------------------

def generate_pdf(df_without, df_with=None, filename="amortization_schedule.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    page_number = 1

    def draw_footer(pageno):
        c.setFont("Helvetica", 9)
        c.drawRightString(width - page_margin_right, 20, f"Page {pageno}")

    def draw_loan_details():
        # --- Loan Details Left Section ---
        c.setFont("Helvetica-Bold", 14)
        c.drawString(page_margin_left, height - 50, "Loan Details:")

        c.setFont("Helvetica", 10)
        c.drawString(page_margin_left, height - 70, f"Principal Amount: {principal:,.2f} Rs")
        c.drawString(page_margin_left, height - 90, f"Monthly EMI: {emi:,.2f} Rs")
        c.drawString(page_margin_left, height - 110, f"Interest Rate (Annual): {interest_rate * 12 * 100:.2f}%")
        c.drawString(page_margin_left, height - 130, f"Loan Period: {loan_period_months // 12} years ({loan_period_months} months)")
        if with_pre_closure in ['Y', 'B']:
            c.drawString(page_margin_left, height - 150, f"Preclosure Amount per year: {preclosure_amount:,.2f} Rs")

        c.line(page_margin_left, height - 160, width - page_margin_right, height - 160)

        # --- Logo + Company Info on Top-Right ---
        logo_width = 100
        logo_height = 40
        logo_x = width - logo_width - page_margin_right
        logo_y = height - 60

        try:
            c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height, preserveAspectRatio=True)
        except Exception as e:
            logger.warning(f"Logo not found or error drawing logo: {e}")

        # Company Info below logo
        text_y_start = logo_y - 5
        line_spacing = 12

        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(width - page_margin_right, text_y_start, company_name)
        c.setFont("Helvetica", 9)
        c.drawRightString(width - page_margin_right, text_y_start - line_spacing, company_address)
        c.drawRightString(width - page_margin_right, text_y_start - 2 * line_spacing, f"Email: {company_email}")
        c.drawRightString(width - page_margin_right, text_y_start - 3 * line_spacing, f"Phone: {company_phone}")

    def draw_table(df, title, show_loan_details=False):
        nonlocal page_number
        rows = df.values.tolist()
        headers = list(df.columns)
        total_rows = len(rows)
        global_row_index = 0
        page = 0

        while global_row_index < total_rows:
            page += 1
            c.setFont("Helvetica", 10)

            if page == 1 and show_loan_details:
                draw_loan_details()
                y = height - 180
                max_rows = int((height - 180 - 60) / row_height)
            else:
                y = height - 50
                max_rows = int((height - 50 - 60) / row_height)

            if page == 1:
                c.setFont("Helvetica-Bold", 12)
                c.drawString(page_margin_left, y, title)
                c.setFont("Helvetica", 10)
                y -= row_height

            # Draw top horizontal line above headers (shifted 3 pts up)
            header_top_y = y + 10
            c.setStrokeColor(colors.black)
            c.setLineWidth(1)
            c.line(page_margin_left, header_top_y, width - page_margin_right, header_top_y)

            # Draw table headers bold and centered horizontally
            c.setFont("Helvetica-Bold", 10)
            for j, header in enumerate(headers):
                start_x = page_margin_left + sum(column_widths[:j])
                col_width = column_widths[j]
                text_width = c.stringWidth(str(header), "Helvetica-Bold", 10)
                text_x = start_x + (col_width - text_width) / 2
                c.drawString(text_x, y, str(header))

            # Draw bottom horizontal line below headers (also shifted up by 3 pts)
            header_bottom_y = y - row_height + 11
            c.line(page_margin_left, header_bottom_y, width - page_margin_right, header_bottom_y)

            c.setFont("Helvetica", 10)
            y -= row_height

            rows_on_this_page = 0
            while rows_on_this_page < max_rows and global_row_index < total_rows:
                row = rows[global_row_index]
                current_month = row[0]
                is_year_end = current_month % 12 == 0
                needed_space = row_height + (20 if is_year_end else 0)

                if y - needed_space < 60:
                    break

                for j, cell in enumerate(row):
                    x_pos = page_margin_left + sum(column_widths[:j])
                    if j == 0:
                        # Left align month
                        c.drawString(x_pos, y, str(cell))
                    else:
                        # Right align values with "Rs" at end
                        c.drawRightString(x_pos + column_widths[j] - 5, y, f"{cell:,.2f} Rs")
                y -= row_height

                if is_year_end:
                    line_y = y - 5 + 10
                    c.setStrokeColor(colors.lightgrey)
                    c.line(page_margin_left, line_y, width - page_margin_right, line_y)
                    c.setStrokeColor(colors.black)
                    c.setFont("Helvetica-Oblique", 9)
                    c.drawString(page_margin_left + 5, line_y - 12, f"End of Year {current_month // 12}")
                    c.setFont("Helvetica", 10)
                    y = line_y - 26 

                global_row_index += 1
                rows_on_this_page += 1

            draw_footer(page_number)
            page_number += 1

            if global_row_index < total_rows:
                c.showPage()

    # === Generate content ===
    if with_pre_closure == 'B':
        # Only show loan details once
        draw_table(df_without, "Amortization Schedule Without Prepayment", show_loan_details=True)
        c.showPage()
        draw_table(df_with, "Amortization Schedule With Prepayment", show_loan_details=False)
    elif with_pre_closure == 'Y':
        draw_table(df_with, "Amortization Schedule With Prepayment", show_loan_details=True)
    else:
        draw_table(df_without, "Amortization Schedule Without Prepayment", show_loan_details=True)

    # Save PDF
    c.save()

# -----------------------------
# Main Execution
# -----------------------------

df_without = create_amortization_schedule(principal, emi, interest_rate, loan_period_months, preclosure_amount=None, prepayment_interval=prepayment_interval, prepay=False)
df_with = create_amortization_schedule(principal, emi, interest_rate, loan_period_months, preclosure_amount=preclosure_amount, prepayment_interval=prepayment_interval, prepay=True)

generate_pdf(df_without, df_with)
