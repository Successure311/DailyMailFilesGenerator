from flask import Flask, jsonify
import mysql.connector
import os

app = Flask(__name__)

TIDB_CONFIG = {
    'host': os.environ.get('TIDB_HOST', 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com'),
    'user': os.environ.get('TIDB_USER', '2hqkC7CYCyd33Y1.root'),
    'password': os.environ.get('TIDB_PASSWORD', 'ED6Hesm31WIPzd8e'),
    'database': os.environ.get('TIDB_DATABASE', 'DailyStrategyForMailFiles'),
    'port': int(os.environ.get('TIDB_PORT', '4000')),
    'charset': 'utf8mb4'
}

def get_tidb_connection():
    return mysql.connector.connect(**TIDB_CONFIG)

# API: Get all Strategies
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

# API: Get Strategies by DTE/WTE and Symbol
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

# API: Get all margin data
@app.route('/api/margin-data')
def get_margin_data():
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM margin_data")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'status': 'success', 'data': rows})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# API: Get specific margin data by type
@app.route('/api/margin-data/<data_type>')
def get_margin_data_by_type(data_type):
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM margin_data WHERE data_type = %s", (data_type,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return jsonify({'status': 'success', 'data': row})
        else:
            return jsonify({'status': 'error', 'message': 'Not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# API: Get INDEX_MARGIN_DATA
@app.route('/api/index-margin')
def get_index_margin():
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT json_data FROM margin_data WHERE data_type = 'INDEX_MARGIN'")
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

# API: Get STRATEGY_TRADE_COUNT
@app.route('/api/strategy-trade-count')
def get_strategy_trade_count():
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT json_data FROM margin_data WHERE data_type = 'STRATEGY_TRADE_COUNT'")
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

# API: Get STRATEGY_EXPECTANCY
@app.route('/api/strategy-expectancy')
def get_strategy_expectancy():
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT json_data FROM margin_data WHERE data_type = 'STRATEGY_EXPECTANCY'")
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

# API: Get CLIENT_MARGIN_DATA
@app.route('/api/client-margin')
def get_client_margin():
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT json_data FROM margin_data WHERE data_type = 'CLIENT_MARGIN'")
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

# API: Get manual lots
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

# API: Get manual lots by date
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

# API: Health check
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

# API: Get all data (combined)
@app.route('/api/all-data')
def get_all_data():
    try:
        import json
        conn = get_tidb_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all margin data
        cursor.execute("SELECT * FROM margin_data")
        margin_rows = cursor.fetchall()
        
        # Convert JSON strings to objects
        margin_data = {}
        for row in margin_rows:
            margin_data[row['data_type']] = json.loads(row['json_data'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'data': {
                'INDEX_MARGIN_DATA': margin_data.get('INDEX_MARGIN', {}),
                'STRATEGY_TRADE_COUNT': margin_data.get('STRATEGY_TRADE_COUNT', {}),
                'STRATEGY_EXPECTANCY': margin_data.get('STRATEGY_EXPECTANCY', {}),
                'CLIENT_MARGIN_DATA': margin_data.get('CLIENT_MARGIN', [])
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5012)