import pandas as pd

TALLY_GROUPS = {
    'fixed assets': 'asset',
    'current assets': 'asset',
    'bank accounts': 'bank',
    'cash-in-hand': 'asset',
    'cash in hand': 'asset',
    'investments': 'asset',
    'loans & advances (asset)': 'asset',
    'deposits (asset)': 'asset',
    'sundry debtors': 'asset',
    'stock-in-hand': 'asset',
    'capital account': 'liability',
    'loans (liability)': 'liability',
    'loans & advances (liability)': 'liability',
    'current liabilities': 'liability',
    'duties & taxes': 'liability',
    'sundry creditors': 'liability',
    'provisions': 'liability',
    'bank od accounts': 'liability',
    'direct incomes': 'income',
    'indirect incomes': 'income',
    'sales accounts': 'income',
    'direct expenses': 'expense',
    'indirect expenses': 'expense',
    'purchase accounts': 'expense',
    'suspense a/c': 'suspense',
}

def parse_trial_balance(file_path):
    df_raw = pd.read_excel(file_path, header=None)
    company = str(df_raw.iloc[0, 0])
    period  = str(df_raw.iloc[2, 0])
    rows, current_group, current_group_type = [], None, None

    for i in range(7, len(df_raw)):
        row  = df_raw.iloc[i]
        name = str(row[0]).strip() if pd.notna(row[0]) else ''
        if not name or name in ('nan', 'Grand Total'):
            continue
        op_dr = float(row[1]) if pd.notna(row[1]) else 0.0
        op_cr = float(row[2]) if pd.notna(row[2]) else 0.0
        cl_dr = float(row[3]) if pd.notna(row[3]) else 0.0
        cl_cr = float(row[4]) if pd.notna(row[4]) else 0.0
        name_lower = name.lower()
        if name_lower in TALLY_GROUPS:
            current_group      = name
            current_group_type = TALLY_GROUPS[name_lower]
            is_group = True
        else:
            is_group = False
        rows.append({
            'Ledger': name, 'Group': current_group or '—',
            'Group Type': current_group_type or 'unknown',
            'Is Group': is_group,
            'Op Dr': op_dr, 'Op Cr': op_cr,
            'Cl Dr': cl_dr, 'Cl Cr': cl_cr,
        })
    return pd.DataFrame(rows), company, period


def analyze_row(row):
    name       = row['Ledger']
    group      = row['Group']
    gtype      = row['Group Type']
    cl_dr      = row['Cl Dr']
    cl_cr      = row['Cl Cr']
    is_group   = row['Is Group']
    name_lower = name.lower()

    if is_group:
        return 'group', '', '', ''

    if 'difference in opening' in name_lower:
        amt = max(cl_dr, cl_cr)
        if amt > 0:
            return ('critical',
                    f'Opening balance difference of ₹{amt:,.2f}',
                    'Opening balances not entered correctly — Balance Sheet unreliable by this amount.',
                    f'Should be ZERO | Fix: Gateway of Tally → Accounts Info → Ledgers → Alter → Correct opening balances')

    if 'suspense' in name_lower and not is_group:
        amt = max(cl_dr, cl_cr)
        if amt > 0:
            return ('critical',
                    f'Suspense account open ₹{amt:,.2f}',
                    'Unidentified entries in suspense — must be cleared before year end.',
                    'Should be ZERO | Fix: Display → Day Book → Filter Suspense → Move to correct ledgers')

    if gtype in ('asset', 'bank'):
        if 'bank' in name_lower or gtype == 'bank':
            if cl_cr > cl_dr:
                return ('review',
                        f'Bank shows Credit (OD) balance ₹{cl_cr:,.2f}',
                        'Credit in bank = Overdraft. Verify if actually a CC/OD account.',
                        'Should be under Bank OD Accounts | Fix: Change group to "Bank OD Accounts" if OD, else correct entries')
        if 'redemption' in name_lower and cl_cr > 0:
            return ('critical',
                    f'Investment Redemption shows Credit ₹{cl_cr:,.2f} under Assets',
                    'Credit balance in Asset group is wrong.',
                    'Should be under Indirect Incomes | Fix: Move ledger to Indirect Income group')
        if 'debtor' in name_lower and cl_cr > 0:
            return ('review',
                    f'Debtor shows Credit balance ₹{cl_cr:,.2f}',
                    'Debtor with credit = advance received from customer or wrong entry.',
                    'Should be under Current Liabilities (if advance) | Fix: Verify and reclassify')
        if cl_cr > cl_dr and cl_cr > 0 and 'redemption' not in name_lower and 'bank' not in name_lower:
            return ('critical',
                    f'Asset ledger has Credit balance ₹{cl_cr:,.2f}',
                    f'"{name}" is under "{group}" (Asset) but has Credit balance.',
                    f'Should have Debit balance | Fix: Entry may be on wrong side or ledger under wrong group')

    elif gtype == 'liability':
        if ('duties' in name_lower or 'tds' in name_lower) and cl_dr > 0 and cl_dr > cl_cr:
            return ('critical',
                    f'Duties & Taxes Debit balance ₹{cl_dr:,.2f}',
                    'Tax liability showing debit = entry on wrong side.',
                    'Should have Credit balance | Fix: Find TDS voucher → swap Debit and Credit')
        if 'creditor' in name_lower and cl_dr > 0:
            return ('review',
                    f'Creditor shows Debit balance ₹{cl_dr:,.2f}',
                    'Creditor with debit = advance paid to vendor or wrong entry.',
                    'Should have Credit balance | Fix: Verify and correct if wrong entry')
        if cl_dr > cl_cr and cl_dr > 0 and 'drawing' not in name_lower:
            return ('review',
                    f'Liability ledger has Debit balance ₹{cl_dr:,.2f}',
                    f'"{name}" under "{group}" (Liability) should have Credit balance.',
                    f'Should have Credit balance under {group} | Fix: Verify all entries')

    elif gtype == 'income':
        if cl_dr > 0 and cl_dr > cl_cr:
            fix = 'Find entry in Day Book → swap Debit and Credit.'
            if 'bank interest' in name_lower:
                fix = 'Bank Interest entry is reversed → swap Debit/Credit. Move to Indirect Incomes.'
            return ('critical',
                    f'Income ledger has Debit balance ₹{cl_dr:,.2f}',
                    f'"{name}" is Income — must have Credit balance. Entry is reversed.',
                    f'Should have Credit balance under Income group | Fix: {fix}')

    elif gtype == 'expense':
        if 'credit card' in name_lower:
            return ('review',
                    f'Credit Card Payment ₹{cl_dr:,.2f} under Expenses',
                    'Credit Card Payment is a liability, not an expense.',
                    'Should be under Current Liabilities | Fix: Create "Credit Card Payable" ledger')
        if cl_cr > 0 and cl_cr > cl_dr:
            return ('review',
                    f'Expense ledger has Credit balance ₹{cl_cr:,.2f}',
                    f'"{name}" showing credit — possible refund or wrong entry.',
                    f'Should have Debit balance under {group} | Fix: Verify if refund or wrong entry')

    if group == 'Investments' and not is_group and cl_cr > 0 and cl_cr > cl_dr:
        return ('critical',
                f'Investment has Credit balance ₹{cl_cr:,.2f}',
                'Investment is an asset — cannot have Credit balance.',
                'Should have Debit balance | Fix: Check if loss/redemption entry posted to wrong ledger')

    if cl_dr == 0 and cl_cr == 0:
        return ('review', 'Zero balance — no activity', 'Unused ledger or missing entries.',
                'Should be deleted if not needed | Fix: Delete or verify missing entries')

    return ('ok', '', '', '')


def run_analysis(file_path):
    df, company, period = parse_trial_balance(file_path)
    results = df.apply(analyze_row, axis=1, result_type='expand')
    results.columns = ['Status', 'Issue', 'Reason', 'Fix']
    df = pd.concat([df, results], axis=1)

    ledgers  = df[df['Is Group'] == False]
    critical = ledgers[ledgers['Status'] == 'critical'].to_dict('records')
    review   = ledgers[ledgers['Status'] == 'review'].to_dict('records')
    ok       = ledgers[ledgers['Status'] == 'ok'].to_dict('records')
    all_rows = ledgers.to_dict('records')

    summary = {
        'total': len(ledgers),
        'critical': len(critical),
        'review': len(review),
        'ok': len(ok),
    }

    return {
        'company': company,
        'period': period,
        'summary': summary,
        'critical': critical,
        'review': review,
        'ok': ok,
        'all': all_rows,
    }
