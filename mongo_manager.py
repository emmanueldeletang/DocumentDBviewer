"""
Module de connexion et opérations MongoDB
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from bson import ObjectId
from bson.json_util import dumps, loads
from datetime import datetime
import json
from config import Config


class MongoDBManager:
    """Gestionnaire de connexion et opérations MongoDB"""
    
    def __init__(self, uri=None):
        self.uri = uri or Config.MONGO_URI
        self.client = None
        self.connect()
    
    def connect(self):
        """Établit la connexion à MongoDB"""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Test de connexion
            self.client.admin.command('ping')
            return True
        except ConnectionFailure as e:
            raise ConnectionError(f"Impossible de se connecter à MongoDB: {e}")
    
    def disconnect(self):
        """Ferme la connexion"""
        if self.client:
            self.client.close()
    
    def get_databases(self):
        """Retourne la liste des bases de données"""
        try:
            return self.client.list_database_names()
        except OperationFailure as e:
            raise Exception(f"Erreur lors de la récupération des bases: {e}")
    
    def get_collections(self, database_name):
        """Retourne la liste des collections d'une base"""
        try:
            db = self.client[database_name]
            return db.list_collection_names()
        except OperationFailure as e:
            raise Exception(f"Erreur lors de la récupération des collections: {e}")
    
    def get_collection_stats(self, database_name, collection_name):
        """Retourne les statistiques d'une collection"""
        try:
            db = self.client[database_name]
            stats = db.command("collStats", collection_name)
            return {
                'count': stats.get('count', 0),
                'size': stats.get('size', 0),
                'avgObjSize': stats.get('avgObjSize', 0),
                'storageSize': stats.get('storageSize', 0)
            }
        except Exception:
            # Si collStats échoue, utiliser count_documents
            db = self.client[database_name]
            count = db[collection_name].count_documents({})
            return {'count': count, 'size': 0, 'avgObjSize': 0, 'storageSize': 0}
    
    def get_documents(self, database_name, collection_name, query=None, 
                      skip=0, limit=20, sort_field="_id", sort_order=-1):
        """Récupère les documents d'une collection avec pagination"""
        try:
            db = self.client[database_name]
            collection = db[collection_name]
            query = query or {}
            
            cursor = collection.find(query).sort(sort_field, sort_order).skip(skip).limit(limit)
            total = collection.count_documents(query)
            
            documents = []
            for doc in cursor:
                documents.append(self._serialize_document(doc))
            
            return {
                'documents': documents,
                'total': total,
                'skip': skip,
                'limit': limit
            }
        except Exception as e:
            raise Exception(f"Erreur lors de la récupération des documents: {e}")
    
    def get_document_by_id(self, database_name, collection_name, doc_id):
        """Récupère un document par son ID"""
        try:
            db = self.client[database_name]
            collection = db[collection_name]
            
            # Essayer avec ObjectId
            try:
                object_id = ObjectId(doc_id)
                doc = collection.find_one({'_id': object_id})
            except:
                doc = collection.find_one({'_id': doc_id})
            
            if doc:
                return self._serialize_document(doc)
            return None
        except Exception as e:
            raise Exception(f"Erreur lors de la récupération du document: {e}")
    
    def insert_document(self, database_name, collection_name, document):
        """Insère un nouveau document"""
        try:
            db = self.client[database_name]
            collection = db[collection_name]
            
            # Ajouter des métadonnées
            document['_created_at'] = datetime.utcnow()
            document['_updated_at'] = datetime.utcnow()
            
            result = collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            raise Exception(f"Erreur lors de l'insertion: {e}")
    
    def update_document(self, database_name, collection_name, doc_id, updates):
        """Met à jour un document"""
        try:
            db = self.client[database_name]
            collection = db[collection_name]
            
            # Ajouter timestamp de mise à jour
            updates['_updated_at'] = datetime.utcnow()
            
            # Essayer avec ObjectId
            try:
                object_id = ObjectId(doc_id)
                query = {'_id': object_id}
            except:
                query = {'_id': doc_id}
            
            result = collection.update_one(query, {'$set': updates})
            return result.modified_count > 0
        except Exception as e:
            raise Exception(f"Erreur lors de la mise à jour: {e}")
    
    def delete_document(self, database_name, collection_name, doc_id):
        """Supprime un document"""
        try:
            db = self.client[database_name]
            collection = db[collection_name]
            
            # Essayer avec ObjectId
            try:
                object_id = ObjectId(doc_id)
                query = {'_id': object_id}
            except:
                query = {'_id': doc_id}
            
            result = collection.delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            raise Exception(f"Erreur lors de la suppression: {e}")
    
    def bulk_delete(self, database_name, collection_name, doc_ids):
        """Supprime plusieurs documents"""
        try:
            db = self.client[database_name]
            collection = db[collection_name]
            
            object_ids = []
            for doc_id in doc_ids:
                try:
                    object_ids.append(ObjectId(doc_id))
                except:
                    object_ids.append(doc_id)
            
            result = collection.delete_many({'_id': {'$in': object_ids}})
            return result.deleted_count
        except Exception as e:
            raise Exception(f"Erreur lors de la suppression en masse: {e}")
    
    def bulk_update(self, database_name, collection_name, doc_ids, updates):
        """Met à jour plusieurs documents"""
        try:
            db = self.client[database_name]
            collection = db[collection_name]
            
            object_ids = []
            for doc_id in doc_ids:
                try:
                    object_ids.append(ObjectId(doc_id))
                except:
                    object_ids.append(doc_id)
            
            updates['_updated_at'] = datetime.utcnow()
            
            result = collection.update_many(
                {'_id': {'$in': object_ids}},
                {'$set': updates}
            )
            return result.modified_count
        except Exception as e:
            raise Exception(f"Erreur lors de la mise à jour en masse: {e}")
    
    def bulk_insert(self, database_name, collection_name, documents):
        """Insère plusieurs documents"""
        try:
            db = self.client[database_name]
            collection = db[collection_name]
            
            # Ajouter des métadonnées à chaque document
            for doc in documents:
                doc['_created_at'] = datetime.utcnow()
                doc['_updated_at'] = datetime.utcnow()
            
            result = collection.insert_many(documents)
            return len(result.inserted_ids)
        except Exception as e:
            raise Exception(f"Erreur lors de l'insertion en masse: {e}")
    
    def transfer_documents(self, source_db, source_collection, target_db, 
                          target_collection, doc_ids=None, copy=True):
        """Transfère des documents entre collections"""
        try:
            source = self.client[source_db][source_collection]
            target = self.client[target_db][target_collection]
            
            # Construire la requête
            query = {}
            if doc_ids:
                object_ids = []
                for doc_id in doc_ids:
                    try:
                        object_ids.append(ObjectId(doc_id))
                    except:
                        object_ids.append(doc_id)
                query = {'_id': {'$in': object_ids}}
            
            # Récupérer les documents source
            docs = list(source.find(query))
            
            if not docs:
                return 0
            
            # Préparer pour l'insertion (retirer _id pour éviter les conflits)
            docs_to_insert = []
            for doc in docs:
                new_doc = doc.copy()
                original_id = new_doc.pop('_id')
                new_doc['_original_id'] = str(original_id)
                new_doc['_transferred_at'] = datetime.utcnow()
                new_doc['_source_db'] = source_db
                new_doc['_source_collection'] = source_collection
                docs_to_insert.append(new_doc)
            
            # Insérer dans la cible
            result = target.insert_many(docs_to_insert)
            transferred_count = len(result.inserted_ids)
            
            # Si déplacement (pas copie), supprimer de la source
            if not copy and transferred_count > 0:
                source.delete_many(query)
            
            return transferred_count
        except Exception as e:
            raise Exception(f"Erreur lors du transfert: {e}")
    
    def full_text_search(self, database_name, collection_name, search_text, 
                         fields=None, skip=0, limit=20):
        """Recherche plein texte"""
        try:
            db = self.client[database_name]
            collection = db[collection_name]
            
            # Vérifier si un index texte existe
            indexes = collection.index_information()
            has_text_index = any('text' in str(idx.get('key', '')) for idx in indexes.values())
            
            if has_text_index:
                # Utiliser $text search
                query = {'$text': {'$search': search_text}}
                projection = {'score': {'$meta': 'textScore'}}
                cursor = collection.find(query, projection).sort(
                    [('score', {'$meta': 'textScore'})]
                ).skip(skip).limit(limit)
                total = collection.count_documents(query)
            else:
                # Fallback: recherche regex sur les champs spécifiés ou tous les champs string
                if fields:
                    or_conditions = [
                        {field: {'$regex': search_text, '$options': 'i'}} 
                        for field in fields
                    ]
                else:
                    # Rechercher sur tous les champs (sample pour déterminer les champs)
                    sample = collection.find_one()
                    if sample:
                        or_conditions = []
                        for key, value in sample.items():
                            if isinstance(value, str):
                                or_conditions.append(
                                    {key: {'$regex': search_text, '$options': 'i'}}
                                )
                    else:
                        or_conditions = []
                
                query = {'$or': or_conditions} if or_conditions else {}
                cursor = collection.find(query).skip(skip).limit(limit)
                total = collection.count_documents(query) if or_conditions else 0
            
            documents = [self._serialize_document(doc) for doc in cursor]
            
            return {
                'documents': documents,
                'total': total,
                'skip': skip,
                'limit': limit
            }
        except Exception as e:
            raise Exception(f"Erreur lors de la recherche plein texte: {e}")
    
    def metadata_search(self, database_name, collection_name, filters, 
                        skip=0, limit=20):
        """Recherche par métadonnées"""
        try:
            db = self.client[database_name]
            collection = db[collection_name]
            
            query = {}
            
            for field, value in filters.items():
                if value is None or value == '':
                    continue
                
                if field.endswith('_from'):
                    # Date de début
                    actual_field = field.replace('_from', '')
                    if actual_field not in query:
                        query[actual_field] = {}
                    query[actual_field]['$gte'] = datetime.fromisoformat(value)
                elif field.endswith('_to'):
                    # Date de fin
                    actual_field = field.replace('_to', '')
                    if actual_field not in query:
                        query[actual_field] = {}
                    query[actual_field]['$lte'] = datetime.fromisoformat(value)
                elif isinstance(value, str) and not value.startswith('{'):
                    # Recherche texte avec regex
                    query[field] = {'$regex': value, '$options': 'i'}
                else:
                    # Valeur exacte ou objet
                    try:
                        query[field] = json.loads(value) if isinstance(value, str) else value
                    except:
                        query[field] = value
            
            cursor = collection.find(query).skip(skip).limit(limit)
            total = collection.count_documents(query)
            
            documents = [self._serialize_document(doc) for doc in cursor]
            
            return {
                'documents': documents,
                'total': total,
                'skip': skip,
                'limit': limit,
                'query': str(query)
            }
        except Exception as e:
            raise Exception(f"Erreur lors de la recherche par métadonnées: {e}")
    
    def create_text_index(self, database_name, collection_name, fields):
        """Crée un index texte sur les champs spécifiés"""
        try:
            db = self.client[database_name]
            collection = db[collection_name]
            
            index_fields = [(field, 'text') for field in fields]
            collection.create_index(index_fields, name='text_search_index')
            return True
        except Exception as e:
            raise Exception(f"Erreur lors de la création de l'index: {e}")
    
    def get_collection_schema(self, database_name, collection_name, sample_size=100):
        """Analyse le schéma d'une collection basé sur un échantillon"""
        try:
            db = self.client[database_name]
            collection = db[collection_name]
            
            # Échantillonner des documents
            sample = list(collection.aggregate([{'$sample': {'size': sample_size}}]))
            
            if not sample:
                return {}
            
            # Analyser les champs
            schema = {}
            for doc in sample:
                self._analyze_document(doc, schema)
            
            return schema
        except Exception as e:
            raise Exception(f"Erreur lors de l'analyse du schéma: {e}")
    
    def _analyze_document(self, doc, schema, prefix=''):
        """Analyse récursive d'un document pour extraire le schéma"""
        for key, value in doc.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if full_key not in schema:
                schema[full_key] = {'types': set(), 'count': 0, 'sample': None}
            
            schema[full_key]['types'].add(type(value).__name__)
            schema[full_key]['count'] += 1
            
            if schema[full_key]['sample'] is None and value is not None:
                if isinstance(value, (ObjectId, datetime)):
                    schema[full_key]['sample'] = str(value)
                elif not isinstance(value, (dict, list)):
                    schema[full_key]['sample'] = value
            
            if isinstance(value, dict):
                self._analyze_document(value, schema, full_key)
    
    def _serialize_document(self, doc):
        """Sérialise un document pour JSON"""
        return json.loads(dumps(doc))
    
    def execute_query(self, database_name, collection_name, query_str):
        """Exécute une requête MongoDB personnalisée"""
        try:
            db = self.client[database_name]
            collection = db[collection_name]
            
            # Parser la requête JSON
            query = json.loads(query_str)
            
            cursor = collection.find(query).limit(100)
            documents = [self._serialize_document(doc) for doc in cursor]
            
            return {
                'documents': documents,
                'count': len(documents)
            }
        except json.JSONDecodeError:
            raise Exception("Format de requête invalide. Utilisez du JSON valide.")
        except Exception as e:
            raise Exception(f"Erreur lors de l'exécution de la requête: {e}")


# Instance globale
mongo_manager = None

def get_mongo_manager():
    """Retourne l'instance du gestionnaire MongoDB"""
    global mongo_manager
    if mongo_manager is None:
        mongo_manager = MongoDBManager()
    return mongo_manager

def reset_mongo_manager():
    """Réinitialise la connexion MongoDB"""
    global mongo_manager
    if mongo_manager:
        mongo_manager.disconnect()
    mongo_manager = None
