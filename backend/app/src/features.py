import pandas as pd

def add_features(df: pd.DataFrame, q75_monthly: float, service_cols: list) -> pd.DataFrame:
    df = df.copy()
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0)
    df["MonthlyCharges"] = pd.to_numeric(df["MonthlyCharges"], errors="coerce").fillna(0)
    df["tenure"] = pd.to_numeric(df["tenure"], errors="coerce").fillna(0)
    
    df['AvgMonthlyCharge'] = df['TotalCharges'] / (df['tenure'] + 1)
    
    tmp_cols = []
    for col in service_cols:
        if col in df.columns:
            tmp = col + '_num'
            df[tmp] = (df[col] == 'Yes').astype(int)
            tmp_cols.append(tmp)
    
    if 'InternetService' in df.columns:
        df['InternetService_num'] = (df['InternetService'] != 'No').astype(int)
        tmp_cols.append('InternetService_num')
    
    if tmp_cols:
        df['ServiceCount'] = df[tmp_cols].sum(axis=1)
        df = df.drop(columns=tmp_cols)
    else:
        df['ServiceCount'] = 0
    
    df['IsNewCustomer'] = (df['tenure'] <= 6).astype(int)
    df['IsLongTerm'] = (df['tenure'] >= 48).astype(int)
    df['HighMonthlyLowTenure'] = (
        (df['MonthlyCharges'] > q75_monthly) & (df['tenure'] < 12)
    ).astype(int)
    
    df['MonthlyToTotalRatio'] = df['MonthlyCharges'] / (df['TotalCharges'] + 1)
    df['ExpectedTotal'] = df['MonthlyCharges'] * df['tenure']
    df['TotalDiff'] = df['TotalCharges'] - df['ExpectedTotal']
    df['IsMonthToMonth'] = (df['Contract'] == 'Month-to-month').astype(int)
    
    return df