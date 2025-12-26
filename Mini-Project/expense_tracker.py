import os
import logging
from datetime import datetime
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry  # You need to install tkcalendar: pip install tkcalendar

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

EXPENSES_FILE = 'expenses.csv'
INCOME_FILE = 'income.csv'
EXPENSES_COLUMNS = ['date', 'category', 'amount', 'description']
INCOME_COLUMNS = ['date', 'source', 'amount', 'description']

CATEGORIES = ['Food', 'Transport', 'Utilities', 'Entertainment', 'Health', 'Other']
INCOME_SOURCES = ['Salary', 'Business', 'Investment', 'Gift', 'Other']

class FinanceTracker:
    def __init__(self):
        self.expenses_df = pd.DataFrame(columns=EXPENSES_COLUMNS)
        self.income_df = pd.DataFrame(columns=INCOME_COLUMNS)
        self.load_data()

    def load_data(self):
        if os.path.exists(EXPENSES_FILE):
            self.expenses_df = pd.read_csv(EXPENSES_FILE, parse_dates=['date'])
            logging.info("Loaded expenses data.")
        else:
            self.expenses_df.to_csv(EXPENSES_FILE, index=False)
            logging.info("Created new expenses file.")

        if os.path.exists(INCOME_FILE):
            self.income_df = pd.read_csv(INCOME_FILE, parse_dates=['date'])
            logging.info("Loaded income data.")
        else:
            self.income_df.to_csv(INCOME_FILE, index=False)
            logging.info("Created new income file.")

    def save_expense(self, date, category, amount, description):
        try:
            amount = -abs(float(amount))
            date = pd.to_datetime(date)
            if category not in CATEGORIES:
                raise ValueError(f"Category '{category}' is not valid.")
            new_row = {'date': date, 'category': category, 'amount': amount, 'description': description}
            self.expenses_df = pd.concat([self.expenses_df, pd.DataFrame([new_row])], ignore_index=True)
            self.expenses_df.to_csv(EXPENSES_FILE, index=False)
            logging.info(f"Added expense: {new_row}")
            return True, "Expense added successfully."
        except Exception as e:
            logging.error(f"Error adding expense: {e}")
            return False, str(e)

    def save_income(self, date, source, amount, description):
        try:
            amount = abs(float(amount))
            date = pd.to_datetime(date)
            if source not in INCOME_SOURCES:
                raise ValueError(f"Source '{source}' is not valid.")
            new_row = {'date': date, 'source': source, 'amount': amount, 'description': description}
            self.income_df = pd.concat([self.income_df, pd.DataFrame([new_row])], ignore_index=True)
            self.income_df.to_csv(INCOME_FILE, index=False)
            logging.info(f"Added income: {new_row}")
            return True, "Income added successfully."
        except Exception as e:
            logging.error(f"Error adding income: {e}")
            return False, str(e)

    def get_summary(self):
        total_income = self.income_df['amount'].sum()
        total_expenses = self.expenses_df['amount'].sum()
        balance = total_income + total_expenses
        summary = (
            f"Total Income: ${total_income:.2f}\n"
            f"Total Expenses: ${-total_expenses:.2f}\n"
            f"Remaining Balance: ${balance:.2f}"
        )
        logging.info("Generated summary report.")
        return summary

    def get_monthly_report(self, year, month):
        expenses_month = self.expenses_df[
            (self.expenses_df['date'].dt.year == year) & (self.expenses_df['date'].dt.month == month)
        ]
        income_month = self.income_df[
            (self.income_df['date'].dt.year == year) & (self.income_df['date'].dt.month == month)
        ]
        total_expenses = expenses_month['amount'].sum()
        total_income = income_month['amount'].sum()
        balance = total_income + total_expenses
        report = (
            f"Monthly Report for {year}-{month:02d}\n"
            f"Total Income: ${total_income:.2f}\n"
            f"Total Expenses: ${-total_expenses:.2f}\n"
            f"Balance: ${balance:.2f}\n\n"
            "Expenses by Category:\n"
        )
        category_summary = expenses_month.groupby('category')['amount'].sum().abs()
        for cat, amt in category_summary.items():
            report += f"  {cat}: ${amt:.2f}\n"
        logging.info(f"Generated monthly report for {year}-{month:02d}.")
        return report

    def export_report(self, text):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Report As"
        )
        if file_path:
            with open(file_path, 'w') as f:
                f.write(text)
            logging.info(f"Report exported to {file_path}")
            messagebox.showinfo("Export Successful", f"Report saved to {file_path}")

class FinanceApp(tk.Tk):
    def __init__(self, tracker):
        super().__init__()
        self.title("Advanced Expense Tracker")
        self.geometry("600x600")
        self.tracker = tracker
        self.create_widgets()

    def create_widgets(self):
        tab_control = ttk.Notebook(self)
        self.income_tab = ttk.Frame(tab_control)
        self.expense_tab = ttk.Frame(tab_control)
        self.report_tab = ttk.Frame(tab_control)

        tab_control.add(self.income_tab, text='Add Income')
        tab_control.add(self.expense_tab, text='Add Expense')
        tab_control.add(self.report_tab, text='Reports')
        tab_control.pack(expand=1, fill='both')

        self.create_income_tab()
        self.create_expense_tab()
        self.create_report_tab()

    def create_income_tab(self):
        frame = self.income_tab
        ttk.Label(frame, text="Income Source:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.income_source = ttk.Combobox(frame, values=INCOME_SOURCES, state='readonly')
        self.income_source.grid(row=0, column=1, padx=10, pady=10)
        self.income_source.current(0)

        ttk.Label(frame, text="Amount:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.income_amount = ttk.Entry(frame)
        self.income_amount.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(frame, text="Date:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.income_date = DateEntry(frame, date_pattern='yyyy-mm-dd')
        self.income_date.grid(row=2, column=1, padx=10, pady=10)

        ttk.Label(frame, text="Description:").grid(row=3, column=0, padx=10, pady=10, sticky='w')
        self.income_desc = ttk.Entry(frame)
        self.income_desc.grid(row=3, column=1, padx=10, pady=10)

        ttk.Button(frame, text="Add Income", command=self.add_income).grid(row=4, column=0, columnspan=2, pady=20)

    def create_expense_tab(self):
        frame = self.expense_tab
        ttk.Label(frame, text="Expense Category:").grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.expense_category = ttk.Combobox(frame, values=CATEGORIES, state='readonly')
        self.expense_category.grid(row=0, column=1, padx=10, pady=10)
        self.expense_category.current(0)

        ttk.Label(frame, text="Amount:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.expense_amount = ttk.Entry(frame)
        self.expense_amount.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(frame, text="Date:").grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.expense_date = DateEntry(frame, date_pattern='yyyy-mm-dd')
        self.expense_date.grid(row=2, column=1, padx=10, pady=10)

        ttk.Label(frame, text="Description:").grid(row=3, column=0, padx=10, pady=10, sticky='w')
        self.expense_desc = ttk.Entry(frame)
        self.expense_desc.grid(row=3, column=1, padx=10, pady=10)

        ttk.Button(frame, text="Add Expense", command=self.add_expense).grid(row=4, column=0, columnspan=2, pady=20)

    def create_report_tab(self):
        frame = self.report_tab
        ttk.Button(frame, text="Show Summary", command=self.show_summary).pack(pady=10)

        ttk.Label(frame, text="Monthly Report Year:").pack(pady=5)
        self.report_year = ttk.Combobox(frame, values=[str(y) for y in range(2000, datetime.now().year + 1)], state='readonly')
        self.report_year.set(str(datetime.now().year))
        self.report_year.pack()

        ttk.Label(frame, text="Monthly Report Month:").pack(pady=5)
        self.report_month = ttk.Combobox(frame, values=[str(m) for m in range(1, 13)], state='readonly')
        self.report_month.set(str(datetime.now().month))
        self.report_month.pack()

        ttk.Button(frame, text="Show Monthly Report", command=self.show_monthly_report).pack(pady=10)

        self.report_text = tk.Text(frame, height=20, width=70)
        self.report_text.pack(pady=10)

        ttk.Button(frame, text="Export Report", command=self.export_report).pack(pady=10)

    def add_income(self):
        source = self.income_source.get()
        amount = self.income_amount.get()
        date = self.income_date.get_date()
        description = self.income_desc.get()
        success, msg = self.tracker.save_income(date, source, amount, description)
        if success:
            messagebox.showinfo("Success", msg)
            self.income_amount.delete(0, tk.END)
            self.income_desc.delete(0, tk.END)
        else:
            messagebox.showerror("Error", msg)

    def add_expense(self):
        category = self.expense_category.get()
        amount = self.expense_amount.get()
        date = self.expense_date.get_date()
        description = self.expense_desc.get()
        success, msg = self.tracker.save_expense(date, category, amount, description)
        if success:
            messagebox.showinfo("Success", msg)
            self.expense_amount.delete(0, tk.END)
            self.expense_desc.delete(0, tk.END)
        else:
            messagebox.showerror("Error", msg)

    def show_summary(self):
        summary = self.tracker.get_summary()
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, summary)

    def show_monthly_report(self):
        try:
            year = int(self.report_year.get())
            month = int(self.report_month.get())
            report = self.tracker.get_monthly_report(year, month)
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, report)
        except Exception as e:
            messagebox.showerror("Error", f"Invalid year or month: {e}")

    def export_report(self):
        text = self.report_text.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "No report to export.")
            return
        self.tracker.export_report(text)

if __name__ == "__main__":
    try:
        import tkcalendar
    except ImportError:
        messagebox.showerror("Missing Dependency", "Please install tkcalendar:\n\npip install tkcalendar")
        exit(1)

    tracker = FinanceTracker()
    app = FinanceApp(tracker)
    app.mainloop()
