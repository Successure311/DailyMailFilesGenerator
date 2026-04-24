import mysql.connector
import pandas as pd

conn = mysql.connector.connect(
    host='gateway01.ap-southeast-1.prod.aws.tidbcloud.com',
    user='2hqkC7CYCyd33Y1.root',
    password='ED6Hesm31WIPzd8e',
    database='DailyStrategyForMailFiles',
    port=4000,
    ssl_ca=r'C:\Sagar\BackTestCode\TiDB\isrgrootx1.pem'
)
cursor = conn.cursor()

df = pd.read_excel(r'E:\Sagar\TradeFilesForMailGenerator\AllStrategyDetails.xlsx', skiprows=1)
df = df.iloc[:, 2:].dropna(how='all')
df.columns = ['Main Strategy', 'DTE/WTE', 'Segment', 'Strategy', 'Exchange', 'Symbol', 
              'Entry Time', 'Exit Time', 'Strike', 'Option Type', 'Side', 'SL%', 'Remarks']
df = df[df['Strategy'].notna()]

print(f'Found {len(df)} strategies')

count = 0
for idx, row in df.iterrows():
    sl_val = row['SL%'] if pd.notna(row['SL%']) else '0'
    sl_str = str(sl_val).strip()
    if '_' in sl_str:
        sl_final = sl_str
    else:
        try:
            sl_final = str(int(float(sl_val) * 100))
        except:
            sl_final = '0'
    
    cursor.execute('''
        INSERT INTO Strategies (main_strategy, dte_wte, segment, strategy, exchange, symbol, 
        entry_time, exit_time, strike, option_type, side, sl_percent, remarks)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        str(row['Main Strategy']) if pd.notna(row['Main Strategy']) else '',
        int(row['DTE/WTE']) if pd.notna(row['DTE/WTE']) else 0,
        str(row['Segment']) if pd.notna(row['Segment']) else '',
        str(row['Strategy']) if pd.notna(row['Strategy']) else '',
        str(row['Exchange']) if pd.notna(row['Exchange']) else '',
        str(row['Symbol']) if pd.notna(row['Symbol']) else '',
        str(row['Entry Time']) if pd.notna(row['Entry Time']) else '',
        str(row['Exit Time']) if pd.notna(row['Exit Time']) else '',
        str(row['Strike']) if pd.notna(row['Strike']) else 'ATM',
        str(row['Option Type']) if pd.notna(row['Option Type']) else 'CE& PE Both',
        str(row['Side']) if pd.notna(row['Side']) else 'Sell',
        sl_final,
        str(row['Remarks']) if pd.notna(row['Remarks']) else ''
    ))
    count += 1

conn.commit()
print(f'Inserted {count} strategies')

cursor.execute('SHOW TABLES')
tables = cursor.fetchall()
print('\nFinal Tables in DailyStrategyForMailFiles:')
for t in tables:
    print(f'  - {t[0]}')

cursor.close()
conn.close()
print('\nDone!')