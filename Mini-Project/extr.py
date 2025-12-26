"""
Expense & Income Tracker (Splitwise-like) - single-file Tkinter app
Save as: expense_income_tracker.py
Run: python expense_income_tracker.py

Features:
- Add people
- Add expenses (payer, participants — multi-select) with equal split
- Add incomes (recipient)
- Shows lists for people, expenses, incomes
- Computes per-person balance (expenses share vs paid + incomes)
- Save/load data to JSON (tracker_data.json)
- Export CSV

This is a simple, self-contained app without external dependencies.
"""

import json
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Dict, Any

DATA_FILE = "tracker_data.json"
DATE_FORMAT = "%Y-%m-%d"

# ---------------- Data classes -----------------
@dataclass
class Person:
    name: str

@dataclass
class Expense:
    date: str
    description: str
    amount: float
    payer: str
    participants: List[str]

@dataclass
class Income:
    date: str
    description: str
    amount: float
    recipient: str

# ---------------- Storage -----------------
class Storage:
    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.people: List[Person] = []
        self.expenses: List[Expense] = []
        self.incomes: List[Income] = []
        self.load()

    def load(self):
        if not os.path.exists(self.filename):
            self.save()
            return
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
        self.people = [Person(**p) for p in data.get("people", [])]
        self.expenses = [Expense(**e) for e in data.get("expenses", [])]
        self.incomes = [Income(**i) for i in data.get("incomes", [])]

    def save(self):
        data = {
            "people": [asdict(p) for p in self.people],
            "expenses": [asdict(e) for e in self.expenses],
            "incomes": [asdict(i) for i in self.incomes],
        }
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # helpers
    def add_person(self, name: str):
        if any(p.name == name for p in self.people):
            raise ValueError("Person already exists")
        self.people.append(Person(name=name))
        self.save()

    def remove_person(self, name: str):
        self.people = [p for p in self.people if p.name != name]
        # also remove from expenses/incomes where relevant
        self.expenses = [e for e in self.expenses if e.payer != name and name not in e.participants]
        self.incomes = [i for i in self.incomes if i.recipient != name]
        self.save()

    def add_expense(self, date: str, desc: str, amount: float, payer: str, participants: List[str]):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if payer not in [p.name for p in self.people]:
            raise ValueError("Payer not found")
        for part in participants:
            if part not in [p.name for p in self.people]:
                raise ValueError(f"Participant {part} not found")
        self.expenses.append(Expense(date=date, description=desc, amount=amount, payer=payer, participants=participants))
        self.save()

    def remove_expense(self, index: int):
        if 0 <= index < len(self.expenses):
            self.expenses.pop(index)
            self.save()

    def add_income(self, date: str, desc: str, amount: float, recipient: str):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if recipient not in [p.name for p in self.people]:
            raise ValueError("Recipient not found")
        self.incomes.append(Income(date=date, description=desc, amount=amount, recipient=recipient))
        self.save()

    def remove_income(self, index: int):
        if 0 <= index < len(self.incomes):
            self.incomes.pop(index)
            self.save()

# ---------------- Business logic -----------------
def compute_balances(storage: Storage) -> Dict[str, float]:
    # For each person: balance = paid - owes + income_received
    balances: Dict[str, float] = {p.name: 0.0 for p in storage.people}

    # Expenses
    for e in storage.expenses:
        num = len(e.participants)
        if num == 0:
            continue
        share = e.amount / num
        # each participant owes share
        for part in e.participants:
            balances[part] -= share
        # payer paid full amount
        balances[e.payer] += e.amount

    # Incomes: add to recipient
    for inc in storage.incomes:
        balances[inc.recipient] += inc.amount

    # Round to 2 decimals
    for k in balances:
        balances[k] = round(balances[k], 2)
    return balances

# ---------------- GUI -----------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Expense & Income Tracker — Splitwise-like")
        self.geometry("900x600")
        self.resizable(True, True)

        self.storage = Storage()

        self.create_widgets()
        self.refresh_all()

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # People tab
        self.tab_people = ttk.Frame(notebook)
        notebook.add(self.tab_people, text="People")
        self.build_people_tab()

        # Expenses tab
        self.tab_expenses = ttk.Frame(notebook)
        notebook.add(self.tab_expenses, text="Expenses")
        self.build_expenses_tab()

        # Income tab
        self.tab_income = ttk.Frame(notebook)
        notebook.add(self.tab_income, text="Income")
        self.build_income_tab()

        # Summary tab
        self.tab_summary = ttk.Frame(notebook)
        notebook.add(self.tab_summary, text="Summary")
        self.build_summary_tab()

    # ---------- People ----------
    def build_people_tab(self):
        frm = ttk.Frame(self.tab_people)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = ttk.Frame(frm)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        lbl = ttk.Label(left, text="People")
        lbl.pack(anchor=tk.W)

        self.people_listbox = tk.Listbox(left, height=15)
        self.people_listbox.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected_person).pack(side=tk.RIGHT, padx=4, pady=4)

        right = ttk.Frame(frm)
        right.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(right, text="Add person").pack(anchor=tk.W)
        self.person_name_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.person_name_var).pack(fill=tk.X)
        ttk.Button(right, text="Add", command=self.add_person).pack(fill=tk.X, pady=6)

        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)
        ttk.Button(right, text="Export CSV", command=self.export_people_csv).pack(fill=tk.X)

    def add_person(self):
        name = self.person_name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing", "Enter a name")
            return
        try:
            self.storage.add_person(name)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
        self.person_name_var.set("")
        self.refresh_all()

    def remove_selected_person(self):
        sel = self.people_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        name = self.people_listbox.get(idx)
        if not messagebox.askyesno("Confirm", f"Remove {name}? This will also remove related expenses/incomes."):
            return
        self.storage.remove_person(name)
        self.refresh_all()

    def export_people_csv(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')])
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('name\n')
                for p in self.storage.people:
                    f.write(f'{p.name}\n')
            messagebox.showinfo('Export', 'People exported')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    # ---------- Expenses ----------
    def build_expenses_tab(self):
        frm = ttk.Frame(self.tab_expenses)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top = ttk.Frame(frm)
        top.pack(fill=tk.X)

        ttk.Label(top, text='Date (YYYY-MM-DD)').grid(row=0, column=0, sticky=tk.W)
        self.exp_date_var = tk.StringVar(value=datetime.now().strftime(DATE_FORMAT))
        ttk.Entry(top, textvariable=self.exp_date_var).grid(row=1, column=0, sticky=tk.W)

        ttk.Label(top, text='Amount').grid(row=0, column=1, sticky=tk.W)
        self.exp_amount_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.exp_amount_var).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(top, text='Payer').grid(row=0, column=2, sticky=tk.W)
        self.exp_payer_cb = ttk.Combobox(top, values=[], state='readonly')
        self.exp_payer_cb.grid(row=1, column=2, sticky=tk.W)

        ttk.Label(top, text='Description').grid(row=0, column=3, sticky=tk.W)
        self.exp_desc_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.exp_desc_var, width=30).grid(row=1, column=3, sticky=tk.W)

        # Participants listbox
        ttk.Label(top, text='Participants (Ctrl+click to multiselect)').grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(8,0))
        self.exp_participants_lb = tk.Listbox(top, selectmode=tk.MULTIPLE, height=6, exportselection=False)
        self.exp_participants_lb.grid(row=3, column=0, columnspan=2, sticky=tk.W+tk.E)

        ttk.Button(top, text='Add Expense', command=self.add_expense).grid(row=3, column=3, sticky=tk.E)

        # Expenses tree
        tree_frame = ttk.Frame(frm)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(8,0))
        columns = ("date", "desc", "amount", "payer", "participants")
        self.exp_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        for c in columns:
            self.exp_tree.heading(c, text=c.title())
            self.exp_tree.column(c, width=100, anchor=tk.W)
        self.exp_tree.pack(fill=tk.BOTH, expand=True)
        self.exp_tree.bind('<Delete>', self.on_delete_expense)

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text='Remove Selected (Del)', command=self.delete_selected_expense).pack(side=tk.RIGHT)
        ttk.Button(btns, text='Export CSV', command=self.export_expenses_csv).pack(side=tk.LEFT)

    def add_expense(self):
        date = self.exp_date_var.get().strip()
        desc = self.exp_desc_var.get().strip()
        amt = self.exp_amount_var.get().strip()
        payer = self.exp_payer_cb.get().strip()
        sel = self.exp_participants_lb.curselection()
        participants = [self.exp_participants_lb.get(i) for i in sel]

        try:
            # validate date
            datetime.strptime(date, DATE_FORMAT)
        except Exception:
            messagebox.showerror('Error', 'Invalid date. Use YYYY-MM-DD')
            return
        try:
            amt_f = float(amt)
        except Exception:
            messagebox.showerror('Error', 'Invalid amount')
            return
        if not participants:
            messagebox.showerror('Error', 'Select at least one participant')
            return
        try:
            self.storage.add_expense(date=date, desc=desc, amount=amt_f, payer=payer, participants=participants)
        except Exception as e:
            messagebox.showerror('Error', str(e))
            return
        self.exp_amount_var.set("")
        self.exp_desc_var.set("")
        self.refresh_all()

    def on_delete_expense(self, event):
        self.delete_selected_expense()

    def delete_selected_expense(self):
        sel = self.exp_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if not messagebox.askyesno('Confirm', 'Delete selected expense?'):
            return
        self.storage.remove_expense(idx)
        self.refresh_all()

    def export_expenses_csv(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')])
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('date,description,amount,payer,participants\n')
                for e in self.storage.expenses:
                    parts = ';'.join(e.participants)
                    f.write(f'{e.date},{e.description},{e.amount},{e.payer},{parts}\n')
            messagebox.showinfo('Export', 'Expenses exported')
        except Exception as exc:
            messagebox.showerror('Error', str(exc))

    # ---------- Income ----------
    def build_income_tab(self):
        frm = ttk.Frame(self.tab_income)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top = ttk.Frame(frm)
        top.pack(fill=tk.X)

        ttk.Label(top, text='Date (YYYY-MM-DD)').grid(row=0, column=0, sticky=tk.W)
        self.inc_date_var = tk.StringVar(value=datetime.now().strftime(DATE_FORMAT))
        ttk.Entry(top, textvariable=self.inc_date_var).grid(row=1, column=0, sticky=tk.W)

        ttk.Label(top, text='Amount').grid(row=0, column=1, sticky=tk.W)
        self.inc_amount_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.inc_amount_var).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(top, text='Recipient').grid(row=0, column=2, sticky=tk.W)
        self.inc_recipient_cb = ttk.Combobox(top, values=[], state='readonly')
        self.inc_recipient_cb.grid(row=1, column=2, sticky=tk.W)

        ttk.Label(top, text='Description').grid(row=0, column=3, sticky=tk.W)
        self.inc_desc_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.inc_desc_var, width=30).grid(row=1, column=3, sticky=tk.W)

        ttk.Button(top, text='Add Income', command=self.add_income).grid(row=1, column=4, sticky=tk.W, padx=8)

        # Income tree
        tree_frame = ttk.Frame(frm)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(8,0))
        columns = ("date", "desc", "amount", "recipient")
        self.inc_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        for c in columns:
            self.inc_tree.heading(c, text=c.title())
            self.inc_tree.column(c, width=120, anchor=tk.W)
        self.inc_tree.pack(fill=tk.BOTH, expand=True)
        self.inc_tree.bind('<Delete>', self.on_delete_income)

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text='Remove Selected (Del)', command=self.delete_selected_income).pack(side=tk.RIGHT)
        ttk.Button(btns, text='Export CSV', command=self.export_incomes_csv).pack(side=tk.LEFT)

    def add_income(self):
        date = self.inc_date_var.get().strip()
        desc = self.inc_desc_var.get().strip()
        amt = self.inc_amount_var.get().strip()
        recipient = self.inc_recipient_cb.get().strip()
        try:
            datetime.strptime(date, DATE_FORMAT)
        except Exception:
            messagebox.showerror('Error', 'Invalid date. Use YYYY-MM-DD')
            return
        try:
            amt_f = float(amt)
        except Exception:
            messagebox.showerror('Error', 'Invalid amount')
            return
        try:
            self.storage.add_income(date=date, desc=desc, amount=amt_f, recipient=recipient)
        except Exception as e:
            messagebox.showerror('Error', str(e))
            return
        self.inc_amount_var.set("")
        self.inc_desc_var.set("")
        self.refresh_all()

    def on_delete_income(self, event):
        self.delete_selected_income()

    def delete_selected_income(self):
        sel = self.inc_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if not messagebox.askyesno('Confirm', 'Delete selected income?'):
            return
        self.storage.remove_income(idx)
        self.refresh_all()

    def export_incomes_csv(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')])
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('date,description,amount,recipient\n')
                for i in self.storage.incomes:
                    f.write(f'{i.date},{i.description},{i.amount},{i.recipient}\n')
            messagebox.showinfo('Export', 'Incomes exported')
        except Exception as exc:
            messagebox.showerror('Error', str(exc))

    # ---------- Summary ----------
    def build_summary_tab(self):
        frm = ttk.Frame(self.tab_summary)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.summary_tree = ttk.Treeview(frm, columns=("person", "balance"), show='headings')
        self.summary_tree.heading('person', text='Person')
        self.summary_tree.heading('balance', text='Balance')
        self.summary_tree.column('person', width=200)
        self.summary_tree.column('balance', width=120)
        self.summary_tree.pack(fill=tk.BOTH, expand=True)

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text='Refresh', command=self.refresh_summary).pack(side=tk.LEFT)
        ttk.Button(btns, text='Save Snapshot', command=self.save_snapshot).pack(side=tk.RIGHT)

    def save_snapshot(self):
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON', '*.json')])
        if not path:
            return
        data = {
            'balances': compute_balances(self.storage),
            'people': [asdict(p) for p in self.storage.people],
            'expenses': [asdict(e) for e in self.storage.expenses],
            'incomes': [asdict(i) for i in self.storage.incomes]
        }
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo('Saved', 'Snapshot saved')
        except Exception as e:
            messagebox.showerror('Error', str(e))

    # ---------- Refresh UI ----------
    def refresh_all(self):
        # people
        self.people_listbox.delete(0, tk.END)
        for p in self.storage.people:
            self.people_listbox.insert(tk.END, p.name)
        # comboboxes and listbox
        people_names = [p.name for p in self.storage.people]
        self.exp_payer_cb['values'] = people_names
        self.inc_recipient_cb['values'] = people_names

        # participants listbox
        self.exp_participants_lb.delete(0, tk.END)
        for name in people_names:
            self.exp_participants_lb.insert(tk.END, name)

        # expenses tree
        for i in self.exp_tree.get_children():
            self.exp_tree.delete(i)
        for idx, e in enumerate(self.storage.expenses):
            parts = ','.join(e.participants)
            self.exp_tree.insert('', tk.END, iid=str(idx), values=(e.date, e.description, e.amount, e.payer, parts))

        # incomes tree
        for i in self.inc_tree.get_children():
            self.inc_tree.delete(i)
        for idx, inc in enumerate(self.storage.incomes):
            self.inc_tree.insert('', tk.END, iid=str(idx), values=(inc.date, inc.description, inc.amount, inc.recipient))

        self.refresh_summary()

    def refresh_summary(self):
        balances = compute_balances(self.storage)
        for i in self.summary_tree.get_children():
            self.summary_tree.delete(i)
        # show sorted by balance desc
        for person, bal in sorted(balances.items(), key=lambda x: x[1], reverse=True):
            self.summary_tree.insert('', tk.END, values=(person, f"{bal:.2f}"))

# ---------------- Run -----------------
if __name__ == '__main__':
    app = App()
    app.mainloop()
