"""
Application Flask pour la gestion MongoDB
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from functools import wraps
import json
from config import Config
from mongo_manager import get_mongo_manager, reset_mongo_manager, MongoDBManager
from translations import get_translation, get_all_translations, TRANSLATIONS

app = Flask(__name__)
app.config.from_object(Config)


def get_lang():
    """Get current language from session"""
    return session.get('lang', 'en')


def t(key, **kwargs):
    """Shortcut for translation"""
    return get_translation(get_lang(), key, **kwargs)


@app.context_processor
def inject_translations():
    """Inject translation function and current language into all templates"""
    lang = get_lang()
    return {
        't': lambda key, **kwargs: get_translation(lang, key, **kwargs),
        'current_lang': lang,
        'translations': get_all_translations(lang)
    }


def handle_errors(f):
    """Décorateur pour gérer les erreurs"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': str(e)}), 500
            flash(f'{t("error")}: {str(e)}', 'error')
            return redirect(request.referrer or url_for('index'))
    return decorated_function


# ==================== LANGUAGE SELECTION ====================

@app.route('/')
def language_select():
    """Language selection page"""
    if 'lang' in session:
        return redirect(url_for('index'))
    return render_template('language_select.html')


@app.route('/set-language/<lang>')
def set_language(lang):
    """Set the language and redirect to home"""
    if lang in TRANSLATIONS:
        session['lang'] = lang
    return redirect(url_for('index'))


@app.route('/change-language')
def change_language():
    """Show language selection page"""
    return render_template('language_select.html')


# ==================== PAGES WEB ====================

@app.route('/home')
@handle_errors
def index():
    """Page d'accueil - Liste des bases de données"""
    if 'lang' not in session:
        return redirect(url_for('language_select'))
    mongo = get_mongo_manager()
    databases = mongo.get_databases()
    return render_template('index.html', databases=databases)


@app.route('/database/<db_name>')
@handle_errors
def view_database(db_name):
    """Vue d'une base de données - Liste des collections"""
    mongo = get_mongo_manager()
    collections = mongo.get_collections(db_name)
    
    # Obtenir les stats pour chaque collection
    collection_stats = {}
    for coll in collections:
        try:
            collection_stats[coll] = mongo.get_collection_stats(db_name, coll)
        except:
            collection_stats[coll] = {'count': 0}
    
    return render_template('database.html', 
                          database=db_name, 
                          collections=collections,
                          collection_stats=collection_stats)


@app.route('/database/<db_name>/collection/<coll_name>')
@handle_errors
def view_collection(db_name, coll_name):
    """Vue d'une collection - Liste des documents"""
    mongo = get_mongo_manager()
    
    page = request.args.get('page', 1, type=int)
    per_page = Config.ITEMS_PER_PAGE
    skip = (page - 1) * per_page
    
    result = mongo.get_documents(db_name, coll_name, skip=skip, limit=per_page)
    
    # Calculer la pagination
    total_pages = (result['total'] + per_page - 1) // per_page
    
    # Obtenir le schéma de la collection
    schema = mongo.get_collection_schema(db_name, coll_name)
    
    # Convertir les sets en listes pour le template
    for field_info in schema.values():
        field_info['types'] = list(field_info['types'])
    
    return render_template('collection.html',
                          database=db_name,
                          collection=coll_name,
                          documents=result['documents'],
                          total=result['total'],
                          page=page,
                          total_pages=total_pages,
                          schema=schema)


@app.route('/database/<db_name>/collection/<coll_name>/document/<doc_id>')
@handle_errors
def view_document(db_name, coll_name, doc_id):
    """Vue d'un document individuel"""
    mongo = get_mongo_manager()
    document = mongo.get_document_by_id(db_name, coll_name, doc_id)
    
    if not document:
        flash('Document non trouvé', 'error')
        return redirect(url_for('view_collection', db_name=db_name, coll_name=coll_name))
    
    return render_template('document.html',
                          database=db_name,
                          collection=coll_name,
                          document=document,
                          doc_id=doc_id)


@app.route('/database/<db_name>/collection/<coll_name>/new')
@handle_errors
def new_document(db_name, coll_name):
    """Formulaire de création d'un nouveau document"""
    mongo = get_mongo_manager()
    schema = mongo.get_collection_schema(db_name, coll_name)
    
    for field_info in schema.values():
        field_info['types'] = list(field_info['types'])
    
    return render_template('document_form.html',
                          database=db_name,
                          collection=coll_name,
                          document=None,
                          schema=schema,
                          is_new=True)


@app.route('/database/<db_name>/collection/<coll_name>/edit/<doc_id>')
@handle_errors
def edit_document(db_name, coll_name, doc_id):
    """Formulaire d'édition d'un document"""
    mongo = get_mongo_manager()
    document = mongo.get_document_by_id(db_name, coll_name, doc_id)
    schema = mongo.get_collection_schema(db_name, coll_name)
    
    for field_info in schema.values():
        field_info['types'] = list(field_info['types'])
    
    if not document:
        flash('Document non trouvé', 'error')
        return redirect(url_for('view_collection', db_name=db_name, coll_name=coll_name))
    
    return render_template('document_form.html',
                          database=db_name,
                          collection=coll_name,
                          document=document,
                          doc_id=doc_id,
                          schema=schema,
                          is_new=False)


@app.route('/database/<db_name>/collection/<coll_name>/search')
@handle_errors
def search_page(db_name, coll_name):
    """Page de recherche avancée"""
    mongo = get_mongo_manager()
    schema = mongo.get_collection_schema(db_name, coll_name)
    
    for field_info in schema.values():
        field_info['types'] = list(field_info['types'])
    
    return render_template('search.html',
                          database=db_name,
                          collection=coll_name,
                          schema=schema)


@app.route('/database/<db_name>/collection/<coll_name>/bulk')
@handle_errors
def bulk_operations_page(db_name, coll_name):
    """Page des opérations en masse"""
    mongo = get_mongo_manager()
    
    # Obtenir toutes les bases et collections pour le transfert
    databases = mongo.get_databases()
    all_collections = {}
    for db in databases:
        all_collections[db] = mongo.get_collections(db)
    
    return render_template('bulk_operations.html',
                          database=db_name,
                          collection=coll_name,
                          databases=databases,
                          all_collections=all_collections)


# ==================== API REST ====================

@app.route('/api/databases')
@handle_errors
def api_list_databases():
    """API: Liste des bases de données"""
    mongo = get_mongo_manager()
    databases = mongo.get_databases()
    return jsonify({'databases': databases})


@app.route('/api/database/<db_name>/collections')
@handle_errors
def api_list_collections(db_name):
    """API: Liste des collections d'une base"""
    mongo = get_mongo_manager()
    collections = mongo.get_collections(db_name)
    return jsonify({'collections': collections})


@app.route('/api/database/<db_name>/collection/<coll_name>/documents')
@handle_errors
def api_list_documents(db_name, coll_name):
    """API: Liste des documents avec pagination"""
    mongo = get_mongo_manager()
    
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', Config.ITEMS_PER_PAGE, type=int)
    sort_field = request.args.get('sort', '_id')
    sort_order = request.args.get('order', -1, type=int)
    
    result = mongo.get_documents(db_name, coll_name, 
                                 skip=skip, limit=limit,
                                 sort_field=sort_field, sort_order=sort_order)
    return jsonify(result)


@app.route('/api/database/<db_name>/collection/<coll_name>/document/<doc_id>')
@handle_errors
def api_get_document(db_name, coll_name, doc_id):
    """API: Récupérer un document"""
    mongo = get_mongo_manager()
    document = mongo.get_document_by_id(db_name, coll_name, doc_id)
    
    if not document:
        return jsonify({'error': 'Document non trouvé'}), 404
    
    return jsonify(document)


@app.route('/api/database/<db_name>/collection/<coll_name>/document', methods=['POST'])
@handle_errors
def api_create_document(db_name, coll_name):
    """API: Créer un document"""
    mongo = get_mongo_manager()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Données requises'}), 400
    
    doc_id = mongo.insert_document(db_name, coll_name, data)
    return jsonify({'success': True, 'id': doc_id}), 201


@app.route('/api/database/<db_name>/collection/<coll_name>/document/<doc_id>', methods=['PUT'])
@handle_errors
def api_update_document(db_name, coll_name, doc_id):
    """API: Mettre à jour un document"""
    mongo = get_mongo_manager()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Données requises'}), 400
    
    success = mongo.update_document(db_name, coll_name, doc_id, data)
    
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Document non trouvé ou non modifié'}), 404


@app.route('/api/database/<db_name>/collection/<coll_name>/document/<doc_id>', methods=['DELETE'])
@handle_errors
def api_delete_document(db_name, coll_name, doc_id):
    """API: Supprimer un document"""
    mongo = get_mongo_manager()
    success = mongo.delete_document(db_name, coll_name, doc_id)
    
    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Document non trouvé'}), 404


# ==================== API BULK OPERATIONS ====================

@app.route('/api/database/<db_name>/collection/<coll_name>/bulk/delete', methods=['POST'])
@handle_errors
def api_bulk_delete(db_name, coll_name):
    """API: Suppression en masse"""
    mongo = get_mongo_manager()
    data = request.get_json()
    
    doc_ids = data.get('ids', [])
    if not doc_ids:
        return jsonify({'error': 'Liste d\'IDs requise'}), 400
    
    deleted_count = mongo.bulk_delete(db_name, coll_name, doc_ids)
    return jsonify({'success': True, 'deleted_count': deleted_count})


@app.route('/api/database/<db_name>/collection/<coll_name>/bulk/update', methods=['POST'])
@handle_errors
def api_bulk_update(db_name, coll_name):
    """API: Mise à jour en masse"""
    mongo = get_mongo_manager()
    data = request.get_json()
    
    doc_ids = data.get('ids', [])
    updates = data.get('updates', {})
    
    if not doc_ids or not updates:
        return jsonify({'error': 'IDs et mises à jour requises'}), 400
    
    modified_count = mongo.bulk_update(db_name, coll_name, doc_ids, updates)
    return jsonify({'success': True, 'modified_count': modified_count})


@app.route('/api/database/<db_name>/collection/<coll_name>/bulk/insert', methods=['POST'])
@handle_errors
def api_bulk_insert(db_name, coll_name):
    """API: Import en masse"""
    mongo = get_mongo_manager()
    data = request.get_json()
    
    documents = data.get('documents', [])
    
    if not documents:
        return jsonify({'error': 'Documents requis'}), 400
    
    inserted_count = mongo.bulk_insert(db_name, coll_name, documents)
    return jsonify({'success': True, 'inserted_count': inserted_count})


@app.route('/api/database/<db_name>/collection/<coll_name>/transfer', methods=['POST'])
@handle_errors
def api_transfer_documents(db_name, coll_name):
    """API: Transfert de documents"""
    mongo = get_mongo_manager()
    data = request.get_json()
    
    target_db = data.get('target_db')
    target_collection = data.get('target_collection')
    doc_ids = data.get('ids', [])
    copy = data.get('copy', True)  # True = copier, False = déplacer
    
    if not target_db or not target_collection:
        return jsonify({'error': 'Base et collection cible requises'}), 400
    
    transferred_count = mongo.transfer_documents(
        db_name, coll_name,
        target_db, target_collection,
        doc_ids if doc_ids else None,
        copy
    )
    
    return jsonify({
        'success': True, 
        'transferred_count': transferred_count,
        'operation': 'copy' if copy else 'move'
    })


# ==================== API SEARCH ====================

@app.route('/api/database/<db_name>/collection/<coll_name>/search/fulltext', methods=['GET', 'POST'])
@handle_errors
def api_fulltext_search(db_name, coll_name):
    """API: Recherche plein texte"""
    mongo = get_mongo_manager()
    
    if request.method == 'POST':
        data = request.get_json()
        search_text = data.get('query', '')
        fields = data.get('fields', None)
        skip = data.get('skip', 0)
        limit = data.get('limit', Config.ITEMS_PER_PAGE)
    else:
        search_text = request.args.get('q', '')
        fields = request.args.getlist('fields') or None
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', Config.ITEMS_PER_PAGE, type=int)
    
    if not search_text:
        return jsonify({'error': 'Requête de recherche requise'}), 400
    
    result = mongo.full_text_search(db_name, coll_name, search_text, fields, skip, limit)
    return jsonify(result)


@app.route('/api/database/<db_name>/collection/<coll_name>/search/metadata', methods=['GET', 'POST'])
@handle_errors
def api_metadata_search(db_name, coll_name):
    """API: Recherche par métadonnées"""
    mongo = get_mongo_manager()
    
    if request.method == 'POST':
        data = request.get_json()
        filters = data.get('filters', {})
        skip = data.get('skip', 0)
        limit = data.get('limit', Config.ITEMS_PER_PAGE)
    else:
        # Construire les filtres depuis les query params
        filters = {}
        for key in request.args:
            if key not in ['skip', 'limit']:
                filters[key] = request.args.get(key)
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', Config.ITEMS_PER_PAGE, type=int)
    
    result = mongo.metadata_search(db_name, coll_name, filters, skip, limit)
    return jsonify(result)


@app.route('/api/database/<db_name>/collection/<coll_name>/search/query', methods=['POST'])
@handle_errors
def api_custom_query(db_name, coll_name):
    """API: Requête MongoDB personnalisée"""
    mongo = get_mongo_manager()
    data = request.get_json()
    
    query_str = data.get('query', '{}')
    result = mongo.execute_query(db_name, coll_name, query_str)
    return jsonify(result)


@app.route('/api/database/<db_name>/collection/<coll_name>/schema')
@handle_errors
def api_get_schema(db_name, coll_name):
    """API: Obtenir le schéma de la collection"""
    mongo = get_mongo_manager()
    schema = mongo.get_collection_schema(db_name, coll_name)
    
    # Convertir les sets en listes pour JSON
    for field_info in schema.values():
        field_info['types'] = list(field_info['types'])
    
    return jsonify(schema)


@app.route('/api/database/<db_name>/collection/<coll_name>/index/text', methods=['POST'])
@handle_errors
def api_create_text_index(db_name, coll_name):
    """API: Créer un index texte"""
    mongo = get_mongo_manager()
    data = request.get_json()
    
    fields = data.get('fields', [])
    if not fields:
        return jsonify({'error': 'Champs requis pour l\'index'}), 400
    
    mongo.create_text_index(db_name, coll_name, fields)
    return jsonify({'success': True})


# ==================== ACTIONS FORMULAIRES ====================

@app.route('/action/document/save', methods=['POST'])
@handle_errors
def action_save_document():
    """Action: Sauvegarder un document (nouveau ou existant)"""
    mongo = get_mongo_manager()
    
    db_name = request.form.get('database')
    coll_name = request.form.get('collection')
    doc_id = request.form.get('doc_id')
    doc_json = request.form.get('document_json')
    
    try:
        document = json.loads(doc_json)
    except json.JSONDecodeError:
        flash('JSON invalide', 'error')
        return redirect(request.referrer)
    
    # Supprimer _id si présent (sera géré par MongoDB)
    document.pop('_id', None)
    
    if doc_id:
        # Mise à jour
        mongo.update_document(db_name, coll_name, doc_id, document)
        flash('Document mis à jour avec succès', 'success')
        return redirect(url_for('view_document', db_name=db_name, coll_name=coll_name, doc_id=doc_id))
    else:
        # Création
        new_id = mongo.insert_document(db_name, coll_name, document)
        flash('Document créé avec succès', 'success')
        return redirect(url_for('view_document', db_name=db_name, coll_name=coll_name, doc_id=new_id))


@app.route('/action/document/delete', methods=['POST'])
@handle_errors
def action_delete_document():
    """Action: Supprimer un document"""
    mongo = get_mongo_manager()
    
    db_name = request.form.get('database')
    coll_name = request.form.get('collection')
    doc_id = request.form.get('doc_id')
    
    mongo.delete_document(db_name, coll_name, doc_id)
    flash('Document supprimé avec succès', 'success')
    return redirect(url_for('view_collection', db_name=db_name, coll_name=coll_name))


if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
