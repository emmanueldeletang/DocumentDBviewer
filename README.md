# DocumentDB Viewer - Flask Application

A complete Flask application to manage and explore DocumentDB/MongoDB databases.

**🌍 Available in English, French (Français), and German (Deutsch)**

## Features

### 🗂️ Navigation
- Browse DocumentDB databases
- - <img width="2579" height="711" alt="image" src="https://github.com/user-attachments/assets/ff3df961-4ae4-4fbc-ac24-aa4b86abef86" />

- Explore collections
- View documents with JSON formatting



### ✏️ Editing
- Create new documents
- Edit existing documents (built-in JSON editor)
- Delete individual documents
- **Bulk editing**: modify multiple documents at once
- **Bulk import**: import multiple documents via JSON or file upload
- **Data transfer**: copy or move documents between collections

### 🔍 Search
- **Full-text search** on document content
- **Metadata search** (by date, specific fields)
- **Custom DocumentDB queries** (JSON)
- Date range filters
- Paginated results

### 🌐 Multi-language Support
- Language selection on first visit
- Switch language anytime via navbar dropdown
- Supported languages: English, French, German

### 🔌 REST API
All features are accessible via API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/databases` | GET | List all databases |
| `/api/database/{db}/collections` | GET | List collections in a database |
| `/api/database/{db}/collection/{coll}/documents` | GET | Get documents with pagination |
| `/api/database/{db}/collection/{coll}/document/{id}` | GET | Get a single document |
| `/api/database/{db}/collection/{coll}/document` | POST | Create a document |
| `/api/database/{db}/collection/{coll}/document/{id}` | PUT | Update a document |
| `/api/database/{db}/collection/{coll}/document/{id}` | DELETE | Delete a document |
| `/api/database/{db}/collection/{coll}/bulk/insert` | POST | Bulk insert |
| `/api/database/{db}/collection/{coll}/bulk/update` | POST | Bulk update |
| `/api/database/{db}/collection/{coll}/bulk/delete` | POST | Bulk delete |
| `/api/database/{db}/collection/{coll}/transfer` | POST | Transfer documents |
| `/api/database/{db}/collection/{coll}/search/fulltext` | GET/POST | Full-text search |
| `/api/database/{db}/collection/{coll}/search/metadata` | GET/POST | Metadata search |
| `/api/database/{db}/collection/{coll}/search/query` | POST | Custom MongoDB query |

## Installation

### Prerequisites
- Python 3.8+
- DocumentDB or MongoDB

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configuration

Edit the `config.py` file to configure your MongoDB/DocumentDB connection:

```python
class Config:
    # documentdb
    MONGO_URI = "mongodb+srv://user:password@documentdb.mongodb.net/"
    

```

### Run the application

```bash
python app.py
```

The application will be available at http://localhost:5000

## Project Structure

```
documentdbviewer/
├── app.py              # Main Flask application
├── config.py           # Configuration (MongoDB connection)
├── mongo_manager.py    # MongoDB management module
├── requirements.txt    # Python dependencies
├── README.md           # Documentation
└── templates/          # HTML templates
    ├── base.html           # Base template
    ├── index.html          # Database list
    ├── database.html       # Collections in a database
    ├── collection.html     # Documents in a collection
    ├── document.html       # Document view
    ├── document_form.html  # Edit form
    ├── search.html         # Search page
    └── bulk_operations.html # Bulk operations
```

## API Usage Examples

### Full-text search
```bash
curl -X POST http://localhost:5000/api/database/mydb/collection/mycoll/search/fulltext \
  -H "Content-Type: application/json" \
  -d '{"query": "search term", "limit": 20}'
```

### Bulk import
```bash
curl -X POST http://localhost:5000/api/database/mydb/collection/mycoll/bulk/insert \
  -H "Content-Type: application/json" \
  -d '{"documents": [{"name": "Doc1"}, {"name": "Doc2"}]}'
```

### Transfer documents
```bash
curl -X POST http://localhost:5000/api/database/mydb/collection/source/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "target_db": "mydb",
    "target_collection": "archive",
    "copy": false
  }'
```

## Security

⚠️ **Warning**: This application is intended for internal/development use.
For production deployment:

1. Change the `SECRET_KEY` in `config.py`
2. Disable `DEBUG` mode
3. Configure a WSGI server (Gunicorn, uWSGI)
4. Add user authentication
5. Use HTTPS

## License

MIT

---

# 🇫🇷 Documentation en Français

## DocumentDB Viewer - Application Flask

Une application Flask complète pour gérer et explorer les bases de données DocumentDB/MongoDB.

### Fonctionnalités

#### 🗂️ Navigation
- Parcourir les bases de données DocumentDB
- Explorer les collections
- Visualiser les documents avec formatage JSON

#### ✏️ Édition
- Créer de nouveaux documents
- Modifier les documents existants (éditeur JSON intégré)
- Supprimer des documents individuels
- **Édition en masse** : modifier plusieurs documents à la fois
- **Import en masse** : importer plusieurs documents via JSON ou fichier
- **Transfert de données** : copier ou déplacer des documents entre collections

#### 🔍 Recherche
- **Recherche plein texte** sur le contenu des documents
- **Recherche par métadonnées** (par date, champs spécifiques)
- **Requêtes DocumentDB personnalisées** (JSON)
- Filtres par plage de dates
- Résultats paginés

### Installation

#### Prérequis
- Python 3.8+
- DocumentDB ou MongoDB

#### Installer les dépendances

```bash
pip install -r requirements.txt
```

#### Configuration

Modifiez le fichier `config.py` pour configurer votre connexion :

```python
class Config:
      # documentdb
    MONGO_URI = "mongodb+srv://user:password@documentdb.mongodb.net/"
```

#### Lancer l'application

```bash
python app.py
```

L'application sera disponible sur http://localhost:5000

### Sécurité

⚠️ **Attention** : Cette application est destinée à un usage interne/développement.
Pour un déploiement en production :

1. Changez la `SECRET_KEY` dans `config.py`
2. Désactivez le mode `DEBUG`
3. Configurez un serveur WSGI (Gunicorn, uWSGI)
4. Ajoutez une authentification utilisateur
5. Utilisez HTTPS

---

# 🇩🇪 Dokumentation auf Deutsch

## DocumentDB Viewer - Flask-Anwendung

Eine vollständige Flask-Anwendung zur Verwaltung und Erkundung von DocumentDB/MongoDB-Datenbanken.

### Funktionen

#### 🗂️ Navigation
- DocumentDB-Datenbanken durchsuchen
- Sammlungen erkunden
- Dokumente mit JSON-Formatierung anzeigen

#### ✏️ Bearbeitung
- Neue Dokumente erstellen
- Bestehende Dokumente bearbeiten (integrierter JSON-Editor)
- Einzelne Dokumente löschen
- **Massenbearbeitung**: mehrere Dokumente gleichzeitig ändern
- **Massenimport**: mehrere Dokumente per JSON oder Datei-Upload importieren
- **Datentransfer**: Dokumente zwischen Sammlungen kopieren oder verschieben

#### 🔍 Suche
- **Volltextsuche** im Dokumentinhalt
- **Metadatensuche** (nach Datum, bestimmten Feldern)
- **Benutzerdefinierte DocumentDB-Abfragen** (JSON)
- Datumsbereichsfilter
- Paginierte Ergebnisse

### Installation

#### Voraussetzungen
- Python 3.8+
- DocumentDB oder MongoDB

#### Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

#### Konfiguration

Bearbeiten Sie die Datei `config.py`, um Ihre Verbindung zu konfigurieren:

```python
class Config:
    # documentdb
    MONGO_URI = "mongodb+srv://user:password@documentdb.mongodb.net/"

#### Anwendung starten

```bash
python app.py
```

Die Anwendung ist unter http://localhost:5000 verfügbar

### Sicherheit

⚠️ **Warnung**: Diese Anwendung ist für den internen/Entwicklungsgebrauch gedacht.
Für den Produktionseinsatz:

1. Ändern Sie den `SECRET_KEY` in `config.py`
2. Deaktivieren Sie den `DEBUG`-Modus
3. Konfigurieren Sie einen WSGI-Server (Gunicorn, uWSGI)
4. Fügen Sie Benutzerauthentifizierung hinzu
5. Verwenden Sie HTTPS


