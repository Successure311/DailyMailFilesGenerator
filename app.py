from flask import Flask, render_template, jsonify, request, send_file
import zipfile
import io
import json
import os
import pandas as pd
import mysql.connector

app = Flask(__name__)

# Static files configuration
app.static_folder = 'static'
app.static_url_path = '/static'

TIDB_CONFIG = {
    'host': os.environ.get('TIDB_HOST', 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com'),
    'user': os.environ.get('TIDB_USER', '2hqkC7CYCyd33Y1.root'),
    'password': os.environ.get('TIDB_PASSWORD', 'ED6Hesm31WIPzd8e'),
    'database': os.environ.get('TIDB_DATABASE', 'DailyStrategyForMailFiles'),
    'port': int(os.environ.get('TIDB_PORT', '4000')),
    'charset': 'utf8mb4'
}

def get_tidb_connection():
    config = TIDB_CONFIG.copy()
    # For Render deployment, enable SSL
    if os.environ.get('RENDER') or os.environ.get('PORT'):
        config['ssl_ca'] = '/etc/ssl/certs/ca-certificates.crt'
    return mysql.connector.connect(**config)

def init_tidb_tables():
    conn = get_tidb_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Strategies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            main_strategy VARCHAR(100),
            dte_wte INT,
            segment VARCHAR(50),
            strategy VARCHAR(100),
            exchange VARCHAR(50),
            symbol VARCHAR(50),
            entry_time VARCHAR(20),
            exit_time VARCHAR(20),
            strike VARCHAR(20),
            option_type VARCHAR(50),
            side VARCHAR(20),
            sl_percent VARCHAR(20),
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS MarginData (
            id INT AUTO_INCREMENT PRIMARY KEY,
            data_type VARCHAR(50),
            index_name VARCHAR(50),
            strategy_name VARCHAR(100),
            json_data JSON,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

try:
    init_tidb_tables()
except Exception as e:
    print(f"TiDB initialization error: {e}")

with open('ClientWiseMargin.py', 'r') as f:
    content = f.read()
    exec(content, globals())

def get_all_dates():
    dates = set()
    for file in ['NF_ExpiryDate.csv', 'BNF_ExpiryDate.csv', 'SNX_ExpiryDate.csv']:
        try:
            df = pd.read_csv(file)
            dates.update(df['Date'].dropna().unique())
        except:
            pass
    sorted_dates = sorted(list(dates), key=lambda x: pd.to_datetime(x, format='%d-%m-%Y'))
    return sorted_dates

def load_MarginData_from_tidb():
    global INDEX_MARGIN_DATA, STRATEGY_TRADE_COUNT, STRATEGY_EXPECTANCY, CLIENT_MARGIN_DATA
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT data_type, json_data FROM MarginData WHERE data_type = 'INDEX_MARGIN' LIMIT 1")
        row = cursor.fetchone()
        if row:
            INDEX_MARGIN_DATA = json.loads(row['json_data'])
        
        cursor.execute("SELECT data_type, json_data FROM MarginData WHERE data_type = 'STRATEGY_TRADE_COUNT' LIMIT 1")
        row = cursor.fetchone()
        if row:
            STRATEGY_TRADE_COUNT = json.loads(row['json_data'])
        
        cursor.execute("SELECT data_type, json_data FROM MarginData WHERE data_type = 'STRATEGY_EXPECTANCY' LIMIT 1")
        row = cursor.fetchone()
        if row:
            STRATEGY_EXPECTANCY = json.loads(row['json_data'])
        
        cursor.execute("SELECT data_type, json_data FROM MarginData WHERE data_type = 'CLIENT_MARGIN' LIMIT 1")
        row = cursor.fetchone()
        if row:
            CLIENT_MARGIN_DATA = json.loads(row['json_data'])
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error loading from TiDB: {e}")

def save_MarginData_to_tidb():
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM MarginData WHERE data_type = 'INDEX_MARGIN'")
        cursor.execute("INSERT INTO MarginData (data_type, json_data) VALUES ('INDEX_MARGIN', %s)", 
                       (json.dumps(INDEX_MARGIN_DATA),))
        
        cursor.execute("DELETE FROM MarginData WHERE data_type = 'STRATEGY_TRADE_COUNT'")
        cursor.execute("INSERT INTO MarginData (data_type, json_data) VALUES ('STRATEGY_TRADE_COUNT', %s)", 
                       (json.dumps(STRATEGY_TRADE_COUNT),))
        
        cursor.execute("DELETE FROM MarginData WHERE data_type = 'STRATEGY_EXPECTANCY'")
        cursor.execute("INSERT INTO MarginData (data_type, json_data) VALUES ('STRATEGY_EXPECTANCY', %s)", 
                       (json.dumps(STRATEGY_EXPECTANCY),))
        
        cursor.execute("DELETE FROM MarginData WHERE data_type = 'CLIENT_MARGIN'")
        cursor.execute("INSERT INTO MarginData (data_type, json_data) VALUES ('CLIENT_MARGIN', %s)", 
                       (json.dumps(CLIENT_MARGIN_DATA),))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error saving to TiDB: {e}")

def load_Strategies_from_tidb(dte_wte, symbol):
    Strategies = []
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM Strategies WHERE 1=1"
        params = []
        
        if dte_wte is not None:
            query += " AND dte_wte = %s"
            params.append(dte_wte)
        
        if symbol:
            symbol_upper = symbol.upper()
            if 'BANKNIFTY' in symbol_upper or 'BANK' in symbol_upper:
                query += " AND symbol LIKE %s"
                params.append('%BANKNIFTY%')
            elif 'NIFTY' in symbol_upper:
                query += " AND symbol LIKE %s"
                params.append('%NIFTY%')
            elif 'SENSEX' in symbol_upper:
                query += " AND symbol LIKE %s"
                params.append('%SENSEX%')
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        for row in rows:
            Strategies.append({
                'Main Strategy': row['main_strategy'],
                'DTE/WTE': row['dte_wte'],
                'Segment': row['segment'],
                'Strategy': row['strategy'],
                'Exchange': row['exchange'],
                'Symbol': row['symbol'],
                'Entry Time': row['entry_time'],
                'Exit Time': row['exit_time'],
                'Strike': row['strike'],
                'Option Type': row['option_type'],
                'Side': row['side'],
                'SL%': row['sl_percent'],
                'Remarks': row['remarks']
            })
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error loading Strategies from TiDB: {e}")
    return Strategies

def save_strategy_to_tidb(strategy_data):
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO Strategies (main_strategy, dte_wte, segment, strategy, exchange, symbol, 
            entry_time, exit_time, strike, option_type, side, sl_percent, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            strategy_data.get('Main Strategy'),
            strategy_data.get('DTE/WTE'),
            strategy_data.get('Segment'),
            strategy_data.get('Strategy'),
            strategy_data.get('Exchange'),
            strategy_data.get('Symbol'),
            strategy_data.get('Entry Time'),
            strategy_data.get('Exit Time'),
            strategy_data.get('Strike'),
            strategy_data.get('Option Type'),
            strategy_data.get('Side'),
            strategy_data.get('SL%'),
            strategy_data.get('Remarks')
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error saving strategy to TiDB: {e}")

try:
    load_MarginData_from_tidb()
except Exception as e:
    print(f"TiDB load error (using local fallback): {e}")

ALL_DATES = get_all_dates()

@app.route('/')
def index():
    return render_template('index.html')

# API Endpoints
@app.route('/api/health')
def health():
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/all-data')
def get_all_data():
    try:
        import json
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all margin data
        cursor.execute("SELECT * FROM MarginData")
        margin_rows = cursor.fetchall()
        
        # Convert JSON strings to objects
        MarginData = {}
        for row in margin_rows:
            MarginData[row['data_type']] = json.loads(row['json_data'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'data': {
                'INDEX_MARGIN_DATA': MarginData.get('INDEX_MARGIN', {}),
                'STRATEGY_TRADE_COUNT': MarginData.get('STRATEGY_TRADE_COUNT', {}),
                'STRATEGY_EXPECTANCY': MarginData.get('STRATEGY_EXPECTANCY', {}),
                'CLIENT_MARGIN_DATA': MarginData.get('CLIENT_MARGIN', [])
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/index-margin')
def get_index_margin():
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT json_data FROM MarginData WHERE data_type = 'INDEX_MARGIN'")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            import json
            return jsonify({'status': 'success', 'data': json.loads(row['json_data'])})
        else:
            return jsonify({'status': 'error', 'message': 'Not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/strategy-trade-count')
def get_strategy_trade_count():
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT json_data FROM MarginData WHERE data_type = 'STRATEGY_TRADE_COUNT'")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            import json
            return jsonify({'status': 'success', 'data': json.loads(row['json_data'])})
        else:
            return jsonify({'status': 'error', 'message': 'Not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/strategy-expectancy')
def get_strategy_expectancy():
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT json_data FROM MarginData WHERE data_type = 'STRATEGY_EXPECTANCY'")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            import json
            return jsonify({'status': 'success', 'data': json.loads(row['json_data'])})
        else:
            return jsonify({'status': 'error', 'message': 'Not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/client-margin')
def get_client_margin():
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT json_data FROM MarginData WHERE data_type = 'CLIENT_MARGIN'")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            import json
            return jsonify({'status': 'success', 'data': json.loads(row['json_data'])})
        else:
            return jsonify({'status': 'error', 'message': 'Not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/manual-lots')
def get_manual_lots():
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM manual_lots")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'status': 'success', 'data': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/manual-lots/<date>')
def get_manual_lots_by_date(date):
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM manual_lots WHERE date = %s", (date,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'status': 'success', 'data': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/Strategies')
def get_Strategies():
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Strategies ORDER BY id")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'status': 'success', 'data': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/Strategies/<int:dte_wte>/<symbol>')
def get_Strategies_by_filter(dte_wte, symbol):
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM Strategies WHERE dte_wte = %s"
        params = [dte_wte]
        
        if symbol:
            symbol_upper = symbol.upper()
            if 'BANKNIFTY' in symbol_upper or 'BANK' in symbol_upper:
                query += " AND symbol LIKE %s"
                params.append('%BANKNIFTY%')
            elif 'NIFTY' in symbol_upper:
                query += " AND symbol LIKE %s"
                params.append('%NIFTY%')
            elif 'SENSEX' in symbol_upper:
                query += " AND symbol LIKE %s"
                params.append('%SENSEX%')
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'status': 'success', 'data': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# Keep original routes for web interface

@app.route('/get_data')
def get_data():
    return jsonify({
        'INDEX_MARGIN_DATA': INDEX_MARGIN_DATA,
        'STRATEGY_TRADE_COUNT': STRATEGY_TRADE_COUNT,
        'STRATEGY_EXPECTANCY': STRATEGY_EXPECTANCY,
        'CLIENT_MARGIN_DATA': CLIENT_MARGIN_DATA,
        'ALL_DATES': ALL_DATES
    })

@app.route('/get_lot_data')
def get_lot_data():
    date = request.args.get('date', '')
    result = {}
    for name, file in [('NF', 'NF_ExpiryDate.csv'), ('BNF', 'BNF_ExpiryDate.csv'), ('SNX', 'SNX_ExpiryDate.csv')]:
        try:
            df = pd.read_csv(file)
            row = df[df['Date'] == date]
            if not row.empty:
                result[name] = row.to_dict('records')[0]
            else:
                result[name] = {}
        except:
            result[name] = {}
    return jsonify(result)

MANUAL_LOTS_FILE = 'manual_lots.json'

def load_manual_lots():
    try:
        if os.path.exists(MANUAL_LOTS_FILE):
            with open(MANUAL_LOTS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

@app.route('/get_Strategies_for_date')
def get_Strategies_for_date():
    date = request.args.get('date', '')
    
    try:
        df_nf = pd.read_csv('NF_ExpiryDate.csv')
        row_nf = df_nf[df_nf['Date'] == date]
        nf_dte = int(row_nf.iloc[0]['DTE']) if not row_nf.empty else 0
        
        df_bnf = pd.read_csv('BNF_ExpiryDate.csv')
        row_bnf = df_bnf[df_bnf['Date'] == date]
        bnf_dte = int(row_bnf.iloc[0]['WTE']) if not row_bnf.empty else 0
        
        df_snx = pd.read_csv('SNX_ExpiryDate.csv')
        row_snx = df_snx[df_snx['Date'] == date]
        snx_dte = int(row_snx.iloc[0]['DTE']) if not row_snx.empty else 0
        
        Strategies = get_Strategies_from_tidb()
        
        filtered = []
        seen = set()
        for strat in Strategies:
            main_strategy = str(strat['Main Strategy']).strip().upper()
            dte_wte = strat['DTE/WTE']
            symbol = strat['Symbol'].upper() if strat['Symbol'] else ''
            
            if not main_strategy:
                continue
            
            index_key = None
            if 'BANKNIFTY' in symbol or 'BANK' in symbol:
                index_key = 'BANKNIFTY'
                match_dte = bnf_dte
            elif 'NIFTY' in symbol:
                index_key = 'NIFTY'
                match_dte = nf_dte
            elif 'SENSEX' in symbol:
                index_key = 'SENSEX'
                match_dte = snx_dte
            
            if index_key and match_dte != dte_wte:
                continue
            
            key = (main_strategy, index_key)
            if key not in seen:
                seen.add(key)
                filtered.append({
                    'strategy': main_strategy,
                    'index': index_key
                })
        
        return jsonify({'Strategies': filtered})
    except Exception as e:
        return jsonify({'Strategies': [], 'error': str(e)})

@app.route('/get_strategy_details')
def get_strategy_details():
    date = request.args.get('date', '')
    
    try:
        df_nf = pd.read_csv('NF_ExpiryDate.csv')
        row_nf = df_nf[df_nf['Date'] == date]
        nf_dte = int(row_nf.iloc[0]['DTE']) if not row_nf.empty else 0
        
        df_bnf = pd.read_csv('BNF_ExpiryDate.csv')
        row_bnf = df_bnf[df_bnf['Date'] == date]
        bnf_dte = int(row_bnf.iloc[0]['WTE']) if not row_bnf.empty else 0
        
        df_snx = pd.read_csv('SNX_ExpiryDate.csv')
        row_snx = df_snx[df_snx['Date'] == date]
        snx_dte = int(row_snx.iloc[0]['DTE']) if not row_snx.empty else 0
        
        strategy_file = get_strategy_file_path()
        if strategy_file:
            df_strategy = pd.read_excel(strategy_file, skiprows=1)
            df_strategy = df_strategy.iloc[:, 2:].dropna(how='all')
            df_strategy.columns = ['Main Strategy', 'DTE/WTE', 'Segment', 'Strategy', 'Exchange', 'Symbol', 
                              'Entry Time', 'Exit Time', 'Strike', 'Option Type', 'Side', 'SL%', 'Remarks']
            df_strategy = df_strategy[df_strategy['Strategy'].notna()]
            
            if 'Strike ' in df_strategy.columns and 'Strike' not in df_strategy.columns:
                df_strategy = df_strategy.rename(columns={'Strike ': 'Strike'})
        
        Strategies = get_Strategies_from_tidb()
        
        filtered_Strategies = []
        for strat in Strategies:
            dte_wte = strat['DTE/WTE']
            symbol = strat['Symbol'].upper() if strat['Symbol'] else ''
            
            index_key = None
            if 'BANKNIFTY' in symbol or 'BANK' in symbol:
                index_key = 'BANKNIFTY'
                match_dte = bnf_dte
            elif 'NIFTY' in symbol:
                index_key = 'NIFTY'
                match_dte = nf_dte
            elif 'SENSEX' in symbol:
                index_key = 'SENSEX'
                match_dte = snx_dte
            
            if index_key and match_dte != dte_wte:
                continue
            
            filtered_Strategies.append(strat)
        
        return jsonify({'status': 'success', 'Strategies': filtered_Strategies})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/save_strategy_details', methods=['POST'])
def save_strategy_details():
    data = request.json
    date = data.get('date', '')
    Strategies = data.get('Strategies', [])
    
    strategy_file = get_strategy_file_path()
    
    try:
        df_nf = pd.read_csv('NF_ExpiryDate.csv')
        row_nf = df_nf[df_nf['Date'] == date]
        nf_dte = int(row_nf.iloc[0]['DTE']) if not row_nf.empty else 0
        
        df_bnf = pd.read_csv('BNF_ExpiryDate.csv')
        row_bnf = df_bnf[df_bnf['Date'] == date]
        bnf_dte = int(row_bnf.iloc[0]['WTE']) if not row_bnf.empty else 0
        
        df_snx = pd.read_csv('SNX_ExpiryDate.csv')
        row_snx = df_snx[df_snx['Date'] == date]
        snx_dte = int(row_snx.iloc[0]['DTE']) if not row_snx.empty else 0
        
        if strategy_file:
            df_strategy = pd.read_excel(strategy_file, skiprows=1)
            df_strategy = df_strategy.iloc[:, 2:].dropna(how='all')
            df_strategy.columns = ['Main Strategy', 'DTE/WTE', 'Segment', 'Strategy', 'Exchange', 'Symbol', 
                              'Entry Time', 'Exit Time', 'Strike', 'Option Type', 'Side', 'SL%', 'Remarks']
            df_strategy = df_strategy[df_strategy['Strategy'].notna()]
            
            if 'Strike ' in df_strategy.columns and 'Strike' not in df_strategy.columns:
                df_strategy = df_strategy.rename(columns={'Strike ': 'Strike'})
        else:
            df_strategy = pd.DataFrame()
        
        rows_to_remove = []
        for idx, row in df_strategy.iterrows():
            dte_wte = int(row['DTE/WTE']) if pd.notna(row['DTE/WTE']) else 0
            symbol = str(row['Symbol']).strip().upper() if pd.notna(row['Symbol']) else ''
            
            index_key = None
            if 'BANKNIFTY' in symbol or 'BANK' in symbol:
                index_key = 'BANKNIFTY'
                match_dte = bnf_dte
            elif 'NIFTY' in symbol:
                index_key = 'NIFTY'
                match_dte = nf_dte
            elif 'SENSEX' in symbol:
                index_key = 'SENSEX'
                match_dte = snx_dte
            
            if index_key and match_dte == dte_wte:
                rows_to_remove.append(idx)
        
        df_strategy_filtered = df_strategy.drop(rows_to_remove)
        new_rows = pd.DataFrame(Strategies)
        df_final = pd.concat([df_strategy_filtered, new_rows], ignore_index=True)
        
        if strategy_file:
            df_final.to_excel(strategy_file, index=False, startrow=1)
        
        # Also save new Strategies to TiDB
        conn = get_tidb_connection()
        cursor = conn.cursor()
        for strat in Strategies:
            sl_val = strat.get('SL%', '0')
            sl_str = str(sl_val).strip().replace('%', '')
            if '_' in sl_str:
                sl_final = sl_str
            else:
                try:
                    sl_final = str(int(float(sl_str)))
                except:
                    sl_final = '0'
            
            cursor.execute('''
                INSERT INTO Strategies (main_strategy, dte_wte, segment, strategy, exchange, symbol, 
                entry_time, exit_time, strike, option_type, side, sl_percent, remarks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                strat.get('Main Strategy', ''),
                strat.get('DTE/WTE', 0),
                strat.get('Segment', ''),
                strat.get('Strategy', ''),
                strat.get('Exchange', ''),
                strat.get('Symbol', ''),
                strat.get('Entry Time', ''),
                strat.get('Exit Time', ''),
                strat.get('Strike', 'ATM'),
                strat.get('Option Type', 'CE& PE Both'),
                strat.get('Side', 'Sell'),
                sl_final,
                strat.get('Remarks', '')
            ))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Strategy details saved successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/get_allocation_data')
def get_allocation_data():
    date = request.args.get('date', '')
    try:
        df_nf = pd.read_csv('NF_ExpiryDate.csv')
        row = df_nf[df_nf['Date'] == date]
        if not row.empty:
            entry_day = row.iloc[0]['EntryDay']
        else:
            entry_day = ''
    except:
        entry_day = ''
    
    manual_data = load_manual_lots()
    saved_multiplier = 15
    
    if date and date in manual_data:
        saved_multiplier = manual_data[date].get('marginMultiplier', 15)
    
    result = {
        'entryDay': entry_day,
        'clients': [],
        'savedMarginMultiplier': saved_multiplier
    }
    
    for client in CLIENT_MARGIN_DATA:
        result['clients'].append({
            'code': client['Code'],
            'client_id': client['ClientID'],
            'total_margin': client['TotalMargin'],
            'percent': 10
        })
    
    return jsonify(result)

@app.route('/save_data', methods=['POST'])
def save_data():
    global INDEX_MARGIN_DATA, STRATEGY_TRADE_COUNT, STRATEGY_EXPECTANCY, CLIENT_MARGIN_DATA
    
    data = request.json
    INDEX_MARGIN_DATA = data.get('INDEX_MARGIN_DATA', INDEX_MARGIN_DATA)
    STRATEGY_TRADE_COUNT = data.get('STRATEGY_TRADE_COUNT', STRATEGY_TRADE_COUNT)
    STRATEGY_EXPECTANCY = data.get('STRATEGY_EXPECTANCY', STRATEGY_EXPECTANCY)
    CLIENT_MARGIN_DATA = data.get('CLIENT_MARGIN_DATA', CLIENT_MARGIN_DATA)
    
    with open('ClientWiseMargin.py', 'w') as f:
        f.write('INDEX_MARGIN_DATA = ' + json.dumps(INDEX_MARGIN_DATA, indent=4) + '\n\n')
        f.write('STRATEGY_TRADE_COUNT = ' + json.dumps(STRATEGY_TRADE_COUNT, indent=4) + '\n\n')
        f.write('CLIENT_MARGIN_DATA = ' + json.dumps(CLIENT_MARGIN_DATA, indent=4) + '\n\n')
        f.write('STRATEGY_EXPECTANCY = ' + json.dumps(STRATEGY_EXPECTANCY, indent=4))
    
    try:
        save_MarginData_to_tidb()
    except Exception as e:
        print(f"Error syncing to TiDB: {e}")
    
    return jsonify({'status': 'success'})

@app.route('/calculate_expectancy', methods=['POST'])
def calculate_expectancy():
    data = request.json
    MarginData = data.get('MarginData', {})
    trade_count = data.get('trade_count', {})
    
    expectancy = {}
    
    for index, Strategies in trade_count.items():
        expectancy[index] = {}
        for strategy, count in Strategies.items():
            if count == '' or count is None or count == '-':
                continue
            
            count = int(count) if count else 0
            if count == 0:
                continue
            
            margin = MarginData.get(index, {})
            expiry_m = margin.get('Expiry', {})
            nonexpiry_m = margin.get('Non_Expiry', {})
            
            expectancy[index][strategy] = {
                'Expectancy': '',
                'Non_Expiry_WOH': nonexpiry_m.get('Without_Hedge', 0) * count,
                'Non_Expiry_WH': nonexpiry_m.get('With_Hedge', 0) * count,
                'Expiry_WOH': expiry_m.get('Without_Hedge', 0) * count,
                'Expiry_WH': expiry_m.get('With_Hedge', 0) * count
            }
    
    return jsonify(expectancy)

@app.route('/save_manual_lots', methods=['POST'])
def save_manual_lots():
    data = request.json
    lots_data = data.get('lotsData', {})
    margin_multiplier = data.get('marginMultiplier', 15)
    date = data.get('date', '')
    
    try:
        import os
        manual_lots_file = 'manual_lots.json'
        manual_data = {}
        
        if os.path.exists(manual_lots_file):
            with open(manual_lots_file, 'r') as f:
                manual_data = json.load(f)
        
        if not date:
            return jsonify({'status': 'error', 'message': 'No date selected'})
        
        manual_data[date] = {
            'lotsData': lots_data,
            'marginMultiplier': margin_multiplier
        }
        
        with open(manual_lots_file, 'w') as f:
            json.dump(manual_data, f, indent=4)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/upload_strategy_file', methods=['POST'])
def upload_strategy_file():
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'})
        
        if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            file.save('AllStrategyDetails.xlsx')
            
            try:
                sync_Strategies_to_tidb()
            except Exception as e:
                print(f"Error syncing Strategies to TiDB: {e}")
            
            return jsonify({'status': 'success', 'message': 'File uploaded successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid file type. Please upload .xlsx or .xls file'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def sync_Strategies_to_tidb():
    strategy_file = get_strategy_file_path()
    if not strategy_file:
        return
    
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM Strategies")
        
        df_strategy = pd.read_excel(strategy_file, skiprows=1)
        df_strategy = df_strategy.iloc[:, 2:].dropna(how='all')
        df_strategy.columns = ['Main Strategy', 'DTE/WTE', 'Segment', 'Strategy', 'Exchange', 'Symbol', 
                          'Entry Time', 'Exit Time', 'Strike', 'Option Type', 'Side', 'SL%', 'Remarks']
        df_strategy = df_strategy[df_strategy['Strategy'].notna()]
        
        for idx, row in df_strategy.iterrows():
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
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error in sync_Strategies_to_tidb: {e}")

def get_strategy_file_path():
    if os.path.exists('AllStrategyDetails.xlsx'):
        return 'AllStrategyDetails.xlsx'
    return None

def get_Strategies_from_tidb(dte_wte=None, symbol=None):
    Strategies = []
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM Strategies WHERE 1=1"
        params = []
        
        if dte_wte is not None:
            query += " AND dte_wte = %s"
            params.append(dte_wte)
        
        if symbol:
            symbol_upper = symbol.upper()
            if 'BANKNIFTY' in symbol_upper or 'BANK' in symbol_upper:
                query += " AND symbol LIKE %s"
                params.append('%BANKNIFTY%')
            elif 'NIFTY' in symbol_upper:
                query += " AND symbol LIKE %s"
                params.append('%NIFTY%')
            elif 'SENSEX' in symbol_upper:
                query += " AND symbol LIKE %s"
                params.append('%SENSEX%')
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        for row in rows:
            Strategies.append({
                'Main Strategy': row['main_strategy'],
                'DTE/WTE': row['dte_wte'],
                'Segment': row['segment'],
                'Strategy': row['strategy'],
                'Exchange': row['exchange'],
                'Symbol': row['symbol'],
                'Entry Time': row['entry_time'],
                'Exit Time': row['exit_time'],
                'Strike': row['strike'],
                'Option Type': row['option_type'],
                'Side': row['side'],
                'SL%': row['sl_percent'],
                'Remarks': row['remarks']
            })
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error loading Strategies from TiDB: {e}")
    return Strategies

@app.route('/generate_csv', methods=['POST'])
def generate_csv():
    data = request.json
    lots_data = data.get('lotsData', {})
    date = data.get('date', '')
    client_MarginData = data.get('clientMarginData', [])
    client_strategy_lots = data.get('clientStrategyLots', [])
    strategy_details = data.get('strategyDetails', None)
    
    try:
        if not date:
            return jsonify({'status': 'error', 'message': 'No date selected'})
        
        strategy_file = get_strategy_file_path()
        
        df_nf = pd.read_csv('NF_ExpiryDate.csv')
        row_nf = df_nf[df_nf['Date'] == date]
        nf_expiry = row_nf.iloc[0]['ExpiryDate'] if not row_nf.empty else ''
        nf_dte = int(row_nf.iloc[0]['DTE']) if not row_nf.empty else 0
        
        df_bnf = pd.read_csv('BNF_ExpiryDate.csv')
        row_bnf = df_bnf[df_bnf['Date'] == date]
        bnf_expiry = row_bnf.iloc[0]['ExpiryDate'] if not row_bnf.empty else ''
        bnf_wte = int(row_bnf.iloc[0]['WTE']) if not row_bnf.empty else 0
        
        df_snx = pd.read_csv('SNX_ExpiryDate.csv')
        row_snx = df_snx[df_snx['Date'] == date]
        snx_expiry = row_snx.iloc[0]['ExpiryDate'] if not row_snx.empty else ''
        snx_dte = int(row_snx.iloc[0]['DTE']) if not row_snx.empty else 0
        
        index_dte_map = {
            'NIFTY': {'expiry': nf_expiry, 'dte': nf_dte, 'wte': nf_dte},
            'BANKNIFTY': {'expiry': bnf_expiry, 'dte': bnf_wte, 'wte': bnf_wte},
            'SENSEX': {'expiry': snx_expiry, 'dte': snx_dte, 'wte': snx_dte}
        }
        
        # If temporary strategy details provided, use them
        if strategy_details and len(strategy_details) > 0:
            print(f"DEBUG: Using strategy_details, count={len(strategy_details)}, first item SL%={strategy_details[0].get('SL%')}")
            df_strategy = pd.DataFrame(strategy_details)
        elif strategy_file:
            df_strategy = pd.read_excel(strategy_file, skiprows=1)
            df_strategy = df_strategy.iloc[:, 2:].dropna(how='all')
            df_strategy.columns = ['Main Strategy', 'DTE/WTE', 'Segment', 'Strategy', 'Exchange', 'Symbol', 
                              'Entry Time', 'Exit Time', 'Strike', 'Option Type', 'Side', 'SL%', 'Remarks']
            df_strategy = df_strategy[df_strategy['Strategy'].notna()]
            
            if 'Strike ' in df_strategy.columns and 'Strike' not in df_strategy.columns:
                df_strategy = df_strategy.rename(columns={'Strike ': 'Strike'})
        else:
            # Use Strategies from TiDB
            tidb_Strategies = get_Strategies_from_tidb()
            df_strategy = pd.DataFrame(tidb_Strategies)
        
        client_lot_map = {}
        valid_Strategies = set()
        valid_excel_Strategies = set()
        excel_to_strategy_map = {}
        for csl in client_strategy_lots:
            cid = str(csl.get('clientId', '')).strip()
            strategy = str(csl.get('strategy', '')).strip()
            index_name = str(csl.get('indexName', '')).strip().upper()
            excel_strategy = str(csl.get('excelStrategy', '')).strip().upper()
            strategy_upper = strategy.upper()
            valid_Strategies.add(strategy_upper)
            if excel_strategy:
                valid_excel_Strategies.add(excel_strategy.upper())
                excel_to_strategy_map[excel_strategy.upper()] = strategy_upper
            if not index_name:
                index_name = 'NIFTY'
            key = f"{cid}_{index_name}_{strategy_upper}"
            client_lot_map[key] = csl.get('lot', 1)
            if excel_strategy:
                excel_key = f"{cid}_{index_name}_{excel_strategy.upper()}"
                client_lot_map[excel_key] = csl.get('lot', 1)
        
        mail_files_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'MailFiles')
        os.makedirs(mail_files_dir, exist_ok=True)
        
        created_files = []
        
        for client in client_MarginData:
            client_id = str(client.get('ClientID', ''))
            if not client_id:
                continue
            
            rows_to_export = []
            
            for idx, row in df_strategy.iterrows():
                strategy = str(row['Strategy']) if pd.notna(row['Strategy']) else ''
                dte_wte = int(row['DTE/WTE']) if pd.notna(row['DTE/WTE']) else 0
                symbol = str(row['Symbol']).strip() if pd.notna(row['Symbol']) else ''
                main_strategy = str(row['Main Strategy']).strip() if pd.notna(row['Main Strategy']) else ''
                
                if not symbol:
                    continue
                
                symbol_upper = symbol.upper()
                index_key = None
                if 'BANKNIFTY' in symbol_upper or 'BANK' in symbol_upper:
                    index_key = 'BANKNIFTY'
                elif 'NIFTY' in symbol_upper:
                    index_key = 'NIFTY'
                elif 'SENSEX' in symbol_upper:
                    index_key = 'SENSEX'
                
                if not index_key:
                    continue
                
                main_strategy_upper = main_strategy.upper()
                if valid_excel_Strategies:
                    if main_strategy_upper not in valid_excel_Strategies and main_strategy_upper not in valid_Strategies:
                        continue
                else:
                    if main_strategy_upper not in valid_Strategies:
                        continue
                
                index_info = index_dte_map.get(index_key, {})
                contract_expiry = index_info.get('expiry', '')
                match_dte = index_info.get('dte', 0)
                
                if match_dte != dte_wte:
                    continue
                
                lot_key = f"{client_id}_{index_key}_{main_strategy_upper}"
                lot_value = client_lot_map.get(lot_key, 1)
                
                if lot_value == 0 or lot_value is None or lot_value < 1:
                    continue
                
                new_row = {
                    'Client ID': client_id,
                    'Main Strategy': main_strategy,
                    'DTE/WTE': dte_wte,
                    'Segment': str(row['Segment']) if pd.notna(row['Segment']) else 'Derivatives',
                    'Strategy': strategy,
                    'Exchange': str(row['Exchange']) if pd.notna(row['Exchange']) else 'NSE',
                    'Symbol': symbol,
                    'Contract': contract_expiry,
                    'Entry Time': str(row['Entry Time']) if pd.notna(row['Entry Time']) else '',
                    'Exit Time': str(row['Exit Time']) if pd.notna(row['Exit Time']) else '',
                    'Strike': str(row['Strike']) if pd.notna(row['Strike']) else 'ATM',
                    'Option Type': str(row['Option Type']) if pd.notna(row['Option Type']) else 'CE& PE Both',
                    'Side': str(row['Side']) if pd.notna(row['Side']) else 'Sell',
                    'SL%': '30%',
                    'LOT': lot_value
                }
                
                remarks_val = ''
                if hasattr(row, 'index') and 'Remarks' in row.index:
                    remarks_val = str(row['Remarks']) if pd.notna(row['Remarks']) else ''
                elif isinstance(row, dict):
                    remarks_val = str(row.get('Remarks', '')) if row.get('Remarks', '') else ''
                new_row['Remarks'] = remarks_val
                
                sl_val = row['SL%'] if pd.notna(row['SL%']) else '30%'
                sl_str = str(sl_val).strip()
                
                # Remove % for processing, then add back
                has_percent = '%' in sl_str
                sl_clean = sl_str.replace('%', '')
                
                if '_' in sl_str:
                    new_row['SL%'] = sl_str
                elif sl_clean.replace('.','').replace('-','').isdigit():
                    new_row['SL%'] = sl_clean + '%'
                else:
                    try:
                        new_row['SL%'] = str(int(float(sl_val) * 100)) + '%'
                    except:
                        new_row['SL%'] = '30%'
                
                rows_to_export.append(new_row)
            
            if rows_to_export:
                df_export = pd.DataFrame(rows_to_export)
                csv_buffer = io.StringIO()
                df_export.to_csv(csv_buffer, index=False)
                created_files.append((f'{client_id}.csv', csv_buffer.getvalue()))
        
        if created_files:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for filename, content in created_files:
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    zf.writestr(filename, content)
            zip_buffer.seek(0)
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f'ClientWiseTradeFiles_{date}.zip'
            )
        
        return jsonify({'status': 'error', 'message': 'No trades to export'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5012)