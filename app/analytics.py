from datetime import datetime, timedelta
from .db import get_db_connection

def _build_filter_query(filters):
    """
    Helper function to build a dynamic WHERE clause and parameters from a filters dictionary.
    
    Args:
        filters (dict): Dictionary with optional keys: start_date, end_date, store_id, category_id.
        
    Returns:
        tuple: (where_clause, params, conditions)
    """
    conditions = []
    params = []

    # Safe get, default to None if key isn't present
    start_date = filters.get('start_date')
    end_date = filters.get('end_date')
    store_id = filters.get('store_id')
    category_id = filters.get('category_id')

    if start_date:
        conditions.append('p.purchase_date >= ?')
        params.append(start_date)

    if end_date:
        conditions.append('p.purchase_date <= ?')
        params.append(end_date)

    if store_id:
        conditions.append('p.store_id = ?')
        params.append(store_id)

    if category_id:
        conditions.append('prod.category_id = ?')
        params.append(category_id)

    where_clause = ''
    if conditions:
        where_clause = 'WHERE ' + ' AND '.join(conditions)
        
    return where_clause, params, conditions


def get_kpis(filters=None):
    """
    Retrieves high-level Key Performance Indicators based on provided filters.
    
    Args:
        filters (dict, optional): Dictionary with optional keys: start_date, end_date, store_id, category_id.
    
    Returns:
        dict: A dictionary containing total_spend, average_spend, weekly_spend, and monthly_spend.
    """
    if filters is None:
        filters = {}
        
    conn = get_db_connection()
    where_clause, params, conditions = _build_filter_query(filters)
    
    # ---- Total Spend ----
    total_spend = conn.execute(f'''
        SELECT COALESCE(SUM(p.price), 0) as total, COALESCE(AVG(p.price), 0) as average
        FROM purchases p
        JOIN products prod ON p.product_id = prod.id
        {where_clause}
    ''', params).fetchone()

    # ---- Weekly Spend ----
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    weekly_conditions = conditions.copy() + ['p.purchase_date >= ?']
    weekly_params = params.copy() + [seven_days_ago]
    weekly_where = 'WHERE ' + ' AND '.join(weekly_conditions)

    weekly_spend = conn.execute(f'''
        SELECT COALESCE(SUM(p.price), 0) as total
        FROM purchases p
        JOIN products prod ON p.product_id = prod.id
        {weekly_where}
    ''', weekly_params).fetchone()['total']

    # ---- Monthly Spend ----
    current_month = datetime.now().strftime('%Y-%m')
    monthly_conditions = conditions.copy() + ["strftime('%Y-%m', p.purchase_date) = ?"]
    monthly_params = params.copy() + [current_month]
    monthly_where = 'WHERE ' + ' AND '.join(monthly_conditions)

    monthly_spend = conn.execute(f'''
        SELECT COALESCE(SUM(p.price), 0) as total
        FROM purchases p
        JOIN products prod ON p.product_id = prod.id
        {monthly_where}
    ''', monthly_params).fetchone()['total']

    conn.close()

    return {
        'total_spend': total_spend['total'],
        'average_spend': total_spend['average'],
        'weekly_spend': weekly_spend,
        'monthly_spend': monthly_spend
    }


def get_store_aggregation(filters=None):
    """
    Calculates total spending grouped by Store based on provided filters.
    Extracts the names and totals into separate lists for Chart.js.
    
    Returns:
        dict: A dictionary containing 'raw_data', 'names', 'totals', and 'top_store'.
    """
    if filters is None:
        filters = {}
        
    conn = get_db_connection()
    where_clause, params, _ = _build_filter_query(filters)
    
    store_rows = conn.execute(f'''
        SELECT s.name, SUM(p.price) as total
        FROM purchases p
        JOIN stores s ON p.store_id = s.id
        JOIN products prod ON p.product_id = prod.id
        {where_clause}
        GROUP BY p.store_id
        ORDER BY total DESC
    ''', params).fetchall()
    
    conn.close()
    
    raw_data = [{'name': row['name'], 'total': row['total']} for row in store_rows]
    names = [row['name'] for row in store_rows]
    totals = [row['total'] for row in store_rows]
    top_store = raw_data[0] if raw_data else None

    return {
        'raw_data': raw_data,
        'names': names,
        'totals': totals,
        'top_store': top_store
    }


def get_category_aggregation(filters=None):
    """
    Calculates total spending grouped by Category based on provided filters.
    Extracts the names and totals into separate lists for Chart.js.
    
    Returns:
        dict: A dictionary containing 'raw_data', 'names', 'totals', and 'top_category'.
    """
    if filters is None:
        filters = {}
        
    conn = get_db_connection()
    where_clause, params, _ = _build_filter_query(filters)
    
    category_rows = conn.execute(f'''
        SELECT c.name, SUM(p.price) as total
        FROM purchases p
        JOIN products prod ON p.product_id = prod.id
        JOIN categories c  ON prod.category_id = c.id
        {where_clause}
        GROUP BY c.id
        ORDER BY total DESC
    ''', params).fetchall()
    
    conn.close()
    
    raw_data = [{'name': row['name'], 'total': row['total']} for row in category_rows]
    names = [row['name'] for row in category_rows]
    totals = [row['total'] for row in category_rows]
    top_category = raw_data[0] if raw_data else None

    return {
        'raw_data': raw_data,
        'names': names,
        'totals': totals,
        'top_category': top_category
    }


def get_monthly_trend(filters=None):
    """
    Calculates total spending grouped by Month-Year based on provided filters.
    Extracts the month labels and totals into separate lists for Chart.js.
    
    Returns:
        dict: A dictionary containing 'raw_data', 'labels', and 'totals'.
    """
    if filters is None:
        filters = {}
        
    conn = get_db_connection()
    where_clause, params, conditions = _build_filter_query(filters)
    
    # Must also filter out entries lacking a purchase_date entirely
    trend_conditions = conditions.copy() + ['p.purchase_date IS NOT NULL']
    trend_where = 'WHERE ' + ' AND '.join(trend_conditions)

    trend_rows = conn.execute(f'''
        SELECT strftime('%Y-%m', p.purchase_date) as month, SUM(p.price) as total
        FROM purchases p
        JOIN products prod ON p.product_id = prod.id
        {trend_where}
        GROUP BY month
        ORDER BY month ASC
    ''', params).fetchall()
    
    conn.close()
    
    raw_data = [{'month': row['month'], 'total': row['total']} for row in trend_rows]
    labels = [row['month'] for row in trend_rows]
    totals = [row['total'] for row in trend_rows]

    return {
        'raw_data': raw_data,
        'labels': labels,
        'totals': totals
    }
