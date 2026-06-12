from flask import Flask, render_template, jsonify, request, send_file
import zipfile
import io
import json
import os
import pandas as pd
import datetime

app = Flask(__name__)

# Initialize variables to satisfy linter
INDEX_MARGIN_DATA = {}
STRATEGY_TRADE_COUNT = {}
STRATEGY_EXPECTANCY = {}
CLIENT_MARGIN_DATA = []

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

ALL_DATES = get_all_dates()

@app.route('/')
def index():
    return render_template('index.html')

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

@app.route('/get_strategies_for_date')
def get_strategies_for_date():
    date = request.args.get('date', '')
    strategy_file = get_strategy_file_path()
    
    if not strategy_file:
        return jsonify({'strategies': []})
    
    try:
        df_strategy = pd.read_excel(strategy_file, skiprows=1)
        df_strategy = df_strategy.iloc[:, 2:].dropna(how='all')
        df_strategy.columns = ['Main Strategy', 'DTE/WTE', 'Segment', 'Strategy', 'Exchange', 'Symbol', 
                          'Entry Time', 'Exit Time', 'Strike', 'Option Type', 'Side', 'SL%', 'Remarks']
        df_strategy = df_strategy[df_strategy['Strategy'].notna()]
        
        if 'Strike ' in df_strategy.columns and 'Strike' not in df_strategy.columns:
            df_strategy = df_strategy.rename(columns={'Strike ': 'Strike'})
        
        df_nf = pd.read_csv('NF_ExpiryDate.csv')
        row_nf = df_nf[df_nf['Date'] == date]
        nf_dte = int(row_nf.iloc[0]['DTE']) if not row_nf.empty else 0
        
        df_bnf = pd.read_csv('BNF_ExpiryDate.csv')
        row_bnf = df_bnf[df_bnf['Date'] == date]
        bnf_dte = int(row_bnf.iloc[0]['WTE']) if not row_bnf.empty else 0
        
        df_snx = pd.read_csv('SNX_ExpiryDate.csv')
        row_snx = df_snx[df_snx['Date'] == date]
        snx_dte = int(row_snx.iloc[0]['DTE']) if not row_snx.empty else 0
        
        strategies = []
        for idx, row in df_strategy.iterrows():
            main_strategy = str(row['Main Strategy']).strip().upper() if pd.notna(row['Main Strategy']) else ''
            dte_wte = int(row['DTE/WTE']) if pd.notna(row['DTE/WTE']) else 0
            symbol = str(row['Symbol']).strip().upper() if pd.notna(row['Symbol']) else ''
            
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
            
            if not any(s['strategy'] == main_strategy and s['index'] == index_key for s in strategies):
                strategies.append({
                    'strategy': main_strategy,
                    'index': index_key
                })
        
        return jsonify({'strategies': strategies})
    except Exception as e:
        return jsonify({'strategies': [], 'error': str(e)})

@app.route('/get_strategy_details')
def get_strategy_details():
    date = request.args.get('date', '')
    strategy_file = get_strategy_file_path()
    
    if not strategy_file:
        return jsonify({'status': 'error', 'message': 'No strategy file found'})
    
    try:
        df_strategy = pd.read_excel(strategy_file, skiprows=1)
        df_strategy = df_strategy.iloc[:, 2:].dropna(how='all')
        df_strategy.columns = ['Main Strategy', 'DTE/WTE', 'Segment', 'Strategy', 'Exchange', 'Symbol', 
                          'Entry Time', 'Exit Time', 'Strike', 'Option Type', 'Side', 'SL%', 'Remarks']
        df_strategy = df_strategy[df_strategy['Strategy'].notna()]
        
        if 'Strike ' in df_strategy.columns and 'Strike' not in df_strategy.columns:
            df_strategy = df_strategy.rename(columns={'Strike ': 'Strike'})
        
        df_nf = pd.read_csv('NF_ExpiryDate.csv')
        row_nf = df_nf[df_nf['Date'] == date]
        nf_dte = int(row_nf.iloc[0]['DTE']) if not row_nf.empty else 0
        
        df_bnf = pd.read_csv('BNF_ExpiryDate.csv')
        row_bnf = df_bnf[df_bnf['Date'] == date]
        bnf_dte = int(row_bnf.iloc[0]['WTE']) if not row_bnf.empty else 0
        
        df_snx = pd.read_csv('SNX_ExpiryDate.csv')
        row_snx = df_snx[df_snx['Date'] == date]
        snx_dte = int(row_snx.iloc[0]['DTE']) if not row_snx.empty else 0
        
        strategies = []
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
            
            if index_key and match_dte != dte_wte:
                continue
            
            strategies.append({
                'Main Strategy': str(row['Main Strategy']) if pd.notna(row['Main Strategy']) else '',
                'DTE/WTE': dte_wte,
                'Segment': str(row['Segment']) if pd.notna(row['Segment']) else '',
                'Strategy': str(row['Strategy']) if pd.notna(row['Strategy']) else '',
                'Exchange': str(row['Exchange']) if pd.notna(row['Exchange']) else '',
                'Symbol': str(row['Symbol']) if pd.notna(row['Symbol']) else '',
                'Entry Time': str(row['Entry Time']) if pd.notna(row['Entry Time']) else '',
                'Exit Time': str(row['Exit Time']) if pd.notna(row['Exit Time']) else '',
                'Strike': str(row['Strike']) if pd.notna(row['Strike']) else 'ATM',
                'Option Type': str(row['Option Type']) if pd.notna(row['Option Type']) else 'CE& PE Both',
                'Side': str(row['Side']) if pd.notna(row['Side']) else 'Sell',
                'SL%': '0',
                'Remarks': str(row['Remarks']) if pd.notna(row['Remarks']) else ''
            })
            try:
                sl_val = row['SL%']
                if pd.notna(sl_val):
                    sl_str = str(sl_val)
                    if '_' in sl_str:
                        strategies[-1]['SL%'] = sl_str
                    else:
                        sl_num = float(sl_val)
                        strategies[-1]['SL%'] = str(int(round(sl_num * 100)))
            except:
                strategies[-1]['SL%'] = '0'
        
        return jsonify({'status': 'success', 'strategies': strategies})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/save_strategy_details', methods=['POST'])
def save_strategy_details():
    data = request.json
    date = data.get('date', '')
    strategies = data.get('strategies', [])
    
    strategy_file = get_strategy_file_path()
    if not strategy_file:
        return jsonify({'status': 'error', 'message': 'No strategy file found'})
    
    try:
        df_strategy = pd.read_excel(strategy_file, skiprows=1)
        df_strategy = df_strategy.iloc[:, 2:].dropna(how='all')
        df_strategy.columns = ['Main Strategy', 'DTE/WTE', 'Segment', 'Strategy', 'Exchange', 'Symbol', 
                          'Entry Time', 'Exit Time', 'Strike', 'Option Type', 'Side', 'SL%', 'Remarks']
        df_strategy = df_strategy[df_strategy['Strategy'].notna()]
        
        if 'Strike ' in df_strategy.columns and 'Strike' not in df_strategy.columns:
            df_strategy = df_strategy.rename(columns={'Strike ': 'Strike'})
        
        df_nf = pd.read_csv('NF_ExpiryDate.csv')
        row_nf = df_nf[df_nf['Date'] == date]
        nf_dte = int(row_nf.iloc[0]['DTE']) if not row_nf.empty else 0
        
        df_bnf = pd.read_csv('BNF_ExpiryDate.csv')
        row_bnf = df_bnf[df_bnf['Date'] == date]
        bnf_dte = int(row_bnf.iloc[0]['WTE']) if not row_bnf.empty else 0
        
        df_snx = pd.read_csv('SNX_ExpiryDate.csv')
        row_snx = df_snx[df_snx['Date'] == date]
        snx_dte = int(row_snx.iloc[0]['DTE']) if not row_snx.empty else 0
        
        df_strategy_filtered = df_strategy.copy()
        
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
        
        new_rows = pd.DataFrame(strategies)
        
        df_final = pd.concat([df_strategy_filtered, new_rows], ignore_index=True)
        
        df_final.to_excel(strategy_file, index=False, startrow=1)
        
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
    
    return jsonify({'status': 'success'})

@app.route('/calculate_expectancy', methods=['POST'])
def calculate_expectancy():
    data = request.json
    margin_data = data.get('margin_data', {})
    trade_count = data.get('trade_count', {})
    
    expectancy = {}
    
    for index, strategies in trade_count.items():
        expectancy[index] = {}
        for strategy, count in strategies.items():
            if count == '' or count is None or count == '-':
                continue
            
            count = int(count) if count else 0
            if count == 0:
                continue
            
            margin = margin_data.get(index, {})
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
            return jsonify({'status': 'success', 'message': 'File uploaded successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Invalid file type. Please upload .xlsx or .xls file'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def get_strategy_file_path():
    if os.path.exists('AllStrategyDetails.xlsx'):
        return 'AllStrategyDetails.xlsx'
    return None

@app.route('/generate_csv', methods=['POST'])
def generate_csv():
    data = request.json
    lots_data = data.get('lotsData', {})
    date = data.get('date', '')
    client_margin_data = data.get('clientMarginData', [])
    client_strategy_lots = data.get('clientStrategyLots', [])
    strategy_details = data.get('strategyDetails', None)
    
    try:
        if not date:
            return jsonify({'status': 'error', 'message': 'No date selected'})
        
        strategy_file = get_strategy_file_path()
        if not strategy_file:
            return jsonify({'status': 'error', 'message': 'No strategy file found. Please upload AllStrategyDetails.xlsx'})
        
        df_strategy = pd.read_excel(strategy_file, skiprows=1)
        df_strategy = df_strategy.iloc[:, 2:].dropna(how='all')
        df_strategy.columns = ['Main Strategy', 'DTE/WTE', 'Segment', 'Strategy', 'Exchange', 'Symbol', 
                          'Entry Time', 'Exit Time', 'Strike', 'Option Type', 'Side', 'SL%', 'Remarks']
        df_strategy = df_strategy[df_strategy['Strategy'].notna()]
        
        if 'Strike ' in df_strategy.columns and 'Strike' not in df_strategy.columns:
            df_strategy = df_strategy.rename(columns={'Strike ': 'Strike'})
        
        # If temporary strategy details provided, use them instead of reading from file
        if strategy_details and len(strategy_details) > 0:
            print(f"DEBUG: Using strategy_details, count={len(strategy_details)}, first item SL%={strategy_details[0].get('SL%')}")
            df_strategy = pd.DataFrame(strategy_details)
        
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
        
        client_lot_map = {}
        valid_strategies = set()
        valid_excel_strategies = set()
        excel_to_strategy_map = {}
        for csl in client_strategy_lots:
            cid = str(csl.get('clientId', '')).strip()
            strategy = str(csl.get('strategy', '')).strip()
            index_name = str(csl.get('indexName', '')).strip().upper()
            excel_strategy = str(csl.get('excelStrategy', '')).strip().upper()
            strategy_upper = strategy.upper()
            valid_strategies.add(strategy_upper)
            if excel_strategy:
                valid_excel_strategies.add(excel_strategy.upper())
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
        
        for client in client_margin_data:
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
                if valid_excel_strategies:
                    if main_strategy_upper not in valid_excel_strategies and main_strategy_upper not in valid_strategies:
                        continue
                else:
                    if main_strategy_upper not in valid_strategies:
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
                download_name='ClientWiseTradeFiles_{}.zip'.format(date)
            )
        
        return jsonify({'status': 'error', 'message': 'No trades to export'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/save_lots_excel', methods=['POST'])
def save_lots_excel():
    data = request.json
    date = data.get('date', '')
    client_data = data.get('clientData', [])
    sl_percent = data.get('slPercent', '')
    margin_multiplier = data.get('marginMultiplier', None)
    
    try:
        if not date:
            return jsonify({'status': 'error', 'message': 'No date selected'})
        
        flattened_data = []
        for client in client_data:
            row = {
                'Code': client.get('Code', ''),
                'ClientID': client.get('ClientID', ''),
                'Percentage': client.get('Percentage', 100),
                'Total Margin': client.get('Total Margin', 0)
            }
            
            for strategy in client.get('Strategies', []):
                key = f"{strategy.get('Strategy', '')} ({strategy.get('Index', '')})"
                row[key] = strategy.get('Lot', 0)
            
            flattened_data.append(row)
        
        df = pd.DataFrame(flattened_data)
        
        output = io.BytesIO()
        # Use openpyxl or xlsxwriter. xlsxwriter is usually more robust for formatting.
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Lots Allocation')
            workbook = writer.book
            worksheet = writer.sheets['Lots Allocation']
            
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D7E4BC',
                'border': 1,
                'align': 'center'
            })
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 15)
        
        output.seek(0)
        filename_suffix = sl_percent if sl_percent else date
        filename_suffix = str(filename_suffix).replace('%', '').strip()
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'ClientWiseLots_{filename_suffix}.xlsx'
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0', port=5012)