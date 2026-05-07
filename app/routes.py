from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from . import db
from . import analytics

# Create a master Blueprint for the application
main_bp = Blueprint('main', __name__)


# ==========================================================
# HOME CONTROLLER
# ==========================================================

@main_bp.route('/')
def home():
    """Renders the dashboard metrics on the main page."""
    app_name = "Personal Grocery & Expense Optimizer"
    metrics = analytics.get_kpis()
    
    return render_template('index.html', title=app_name, **metrics)


# ==========================================================
# RESOURCE CONTROLLERS (CRUD Views)
# ==========================================================

@main_bp.route('/stores', methods=('GET', 'POST'))
def stores():
    if request.method == 'POST':
        store_name = request.form.get('store_name', '').strip()
        success, error = db.add_store(store_name)
        if success:
            flash('Store added successfully.', 'success')
            return redirect(url_for('main.stores'))
        else:
            flash(error, 'error')
            return redirect(url_for('main.stores'))

    stores_list = db.get_all_stores()
    return render_template('stores.html', stores=stores_list)


@main_bp.route('/stores/delete/<int:store_id>', methods=['POST'])
def delete_store_action(store_id):
    """Deletes a store if it is not used in any purchases."""
    if db.check_store_in_use(store_id):
        # Store is attached to a purchase, so do not delete.
        flash('Cannot delete store: It is used in existing purchases.', 'error')
    else:
        # Store is safe to delete.
        db.delete_store(store_id)
        flash('Store deleted successfully.', 'success')
        
    return redirect(url_for('main.stores'))

@main_bp.route('/stores/update/<int:store_id>', methods=['POST'])
def update_store_action(store_id):
    """Updates a store's name inline via a JSON request."""
    data = request.get_json()
    new_name = data.get('name', '').strip()
    
    # Validate input
    if not new_name:
        return jsonify({'success': False, 'message': 'Store name cannot be empty'}), 400
        
    # Attempt to update the database
    success, error = db.update_store(store_id, new_name)
    if success:
        return jsonify({'success': True, 'message': 'Store updated successfully', 'name': new_name})
    else:
        return jsonify({'success': False, 'message': error}), 400


@main_bp.route('/categories', methods=('GET', 'POST'))
def categories():
    if request.method == 'POST':
        category_name = request.form.get('category_name', '').strip()
        success, error = db.add_category(category_name)
        if success:
            flash('Category added successfully.', 'success')
            return redirect(url_for('main.categories'))
        else:
            flash(error, 'error')
            return redirect(url_for('main.categories'))

    categories_list = db.get_all_categories()
    return render_template('categories.html', categories=categories_list)


@main_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
def delete_category_action(category_id):
    """Deletes a category if it is not used by any products."""
    if db.check_category_in_use(category_id):
        # Category is attached to products, do not delete
        flash('Cannot delete category: It is used by existing products.', 'error')
    else:
        # Category is safe to delete
        db.delete_category(category_id)
        flash('Category deleted successfully.', 'success')
        
    return redirect(url_for('main.categories'))

@main_bp.route('/categories/update/<int:category_id>', methods=['POST'])
def update_category_action(category_id):
    """Updates a category's name inline via a JSON request."""
    data = request.get_json()
    new_name = data.get('name', '').strip()
    
    # Validate input
    if not new_name:
        return jsonify({'success': False, 'message': 'Category name cannot be empty'}), 400
        
    # Attempt to update the database
    success, error = db.update_category(category_id, new_name)
    if success:
        return jsonify({'success': True, 'message': 'Category updated successfully', 'name': new_name})
    else:
        return jsonify({'success': False, 'message': error}), 400


@main_bp.route('/products', methods=('GET', 'POST'))
def products():
    if request.method == 'POST':
        product_name = request.form.get('product_name', '').strip()
        category_id = request.form.get('category_id')

        success, error = db.add_product(product_name, category_id)
        if success:
            flash('Product added successfully.', 'success')
            return redirect(url_for('main.products'))
        else:
            flash(error, 'error')
            return redirect(url_for('main.products'))

    categories = db.get_all_categories()
    products_list = db.get_products_with_categories()
    
    return render_template('products.html', products=products_list, categories=categories)


@main_bp.route('/products/delete/<int:product_id>', methods=['POST'])
def delete_product_action(product_id):
    """Deletes a product if it is not used in any purchases."""
    if db.check_product_in_use(product_id):
        # Product is attached to a purchase, do not delete
        flash('Cannot delete product: It is used in existing purchases.', 'error')
    else:
        # Product is safe to delete
        db.delete_product(product_id)
        flash('Product deleted successfully.', 'success')
        
    return redirect(url_for('main.products'))

@main_bp.route('/products/update/<int:product_id>', methods=['POST'])
def update_product_action(product_id):
    """Updates a product's name and category via a JSON request."""
    data = request.get_json()
    new_name = data.get('name', '').strip()
    category_id = data.get('category_id')
    
    if not new_name:
        return jsonify({'success': False, 'message': 'Product name cannot be empty'}), 400
        
    success, error = db.update_product(product_id, new_name, category_id)
    if success:
        # Fetch the updated category name for the frontend UI refresh
        conn = db.get_db_connection()
        cat = conn.execute('SELECT name FROM categories WHERE id = ?', (category_id,)).fetchone()
        conn.close()
        cat_name = cat['name'] if cat else 'No Category'
        
        return jsonify({
            'success': True, 
            'message': 'Product updated successfully', 
            'name': new_name,
            'category_name': cat_name
        })
    else:
        return jsonify({'success': False, 'message': error}), 400


@main_bp.route('/purchases', methods=('GET', 'POST'))
def purchases():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        store_id = request.form.get('store_id')
        price = request.form.get('price')
        purchase_date = request.form.get('purchase_date')

        success, error = db.add_purchase(product_id, store_id, price, purchase_date)
        if success:
            flash('Purchase logged successfully.', 'success')
            return redirect(url_for('main.purchases'))
        else:
            flash(error, 'error')
            return redirect(url_for('main.purchases'))

    products = db.get_all_products()
    stores = db.get_all_stores()
    purchases_list = db.get_purchases_with_details()

    return render_template('purchases.html', purchases=purchases_list, products=products, stores=stores)


@main_bp.route('/purchases/delete/<int:purchase_id>', methods=['POST'])
def delete_purchase_action(purchase_id):
    """Deletes a single purchase log."""
    db.delete_purchase(purchase_id)
    flash('Purchase deleted successfully.', 'success')
        
    return redirect(url_for('main.purchases'))

@main_bp.route('/purchases/update/<int:purchase_id>', methods=['POST'])
def update_purchase_action(purchase_id):
    """Updates a purchase record via a JSON request."""
    data = request.get_json()
    product_id = data.get('product_id')
    store_id = data.get('store_id')
    price = data.get('price')
    purchase_date = data.get('purchase_date')
    
    if not product_id or price is None:
        return jsonify({'success': False, 'message': 'Product and Price are required'}), 400
        
    success, error = db.update_purchase(purchase_id, product_id, store_id, price, purchase_date)
    if success:
        # Fetch fresh display names for the frontend refresh
        conn = db.get_db_connection()
        info = conn.execute('''
            SELECT prod.name as product_name, cat.name as category_name, s.name as store_name
            FROM purchases p
            JOIN products prod ON p.product_id = prod.id
            LEFT JOIN categories cat ON prod.category_id = cat.id
            LEFT JOIN stores s ON p.store_id = s.id
            WHERE p.id = ?
        ''', (purchase_id,)).fetchone()
        conn.close()
        
        return jsonify({
            'success': True,
            'product_name': info['product_name'],
            'category_name': info['category_name'] or 'No Category',
            'store_name': info['store_name'] or '-',
            'price': float(price),
            'purchase_date': purchase_date
        })
    else:
        return jsonify({'success': False, 'message': error}), 400


# ==========================================================
# REPORT CONTROLLERS
# ==========================================================

@main_bp.route('/reports')
def reports():
    """Renders the comprehensive visual reports layout."""
    
    # 1. Fetch Aggregated Metrics
    metrics = analytics.get_kpis()
    store_data = analytics.get_store_aggregation()
    category_data = analytics.get_category_aggregation()
    trend_data = analytics.get_monthly_trend()
    
    # 2. Fetch Base Sets for Filters
    all_stores = db.get_all_stores()
    all_categories = db.get_all_categories()
    
    # 3. Inject precisely defined dictionaries into Template
    return render_template('reports.html',
                           total_spend=metrics['total_spend'],
                           weekly_spend=metrics['weekly_spend'],
                           monthly_spend=metrics['monthly_spend'],
                           average_spend=metrics['average_spend'],
                           store_spending=store_data['raw_data'],
                           category_spending=category_data['raw_data'],
                           top_store=store_data['top_store'],
                           top_category=category_data['top_category'],
                           store_names=store_data['names'],
                           store_totals=store_data['totals'],
                           category_names=category_data['names'],
                           category_totals=category_data['totals'],
                           month_labels=trend_data['labels'],
                           monthly_totals=trend_data['totals'],
                           all_stores=all_stores,
                           all_categories=all_categories)


# ==========================================================
# API ENDPOINTS
# ==========================================================

@main_bp.route('/api/reports')
def api_reports():
    """Returns dynamic Chart.js injection data based on user filter parameters."""
    
    filters = {
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'store_id': request.args.get('store_id'),
        'category_id': request.args.get('category_id')
    }
    
    metrics = analytics.get_kpis(filters)
    store_data = analytics.get_store_aggregation(filters)
    cat_data = analytics.get_category_aggregation(filters)
    trend_data = analytics.get_monthly_trend(filters)

    return jsonify({
        'total_spend':     metrics['total_spend'],
        'weekly_spend':    metrics['weekly_spend'],
        'monthly_spend':   metrics['monthly_spend'],
        'store_names':     store_data['names'],
        'store_totals':    store_data['totals'],
        'category_names':  cat_data['names'],
        'category_totals': cat_data['totals'],
        'month_labels':    trend_data['labels'],
        'monthly_totals':  trend_data['totals']
    })
