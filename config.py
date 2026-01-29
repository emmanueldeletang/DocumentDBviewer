# Configuration MongoDB
# Modifiez la chaîne de connexion selon votre environnement

class Config:
    # Chaîne de connexion MongoDB
    # Format: mongodb://[username:password@]host[:port]/[database]
    # Exemples:
    # -
    MONGO_URI =  "mongodb+srv://account:password@your-mongo.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"

    
    # Base de données par défaut (optionnel)
    DEFAULT_DATABASE = None
    
    # Configuration Flask
    SECRET_KEY = "votre-cle-secrete-changez-moi"
    DEBUG = True
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Taille maximale pour l'upload (en bytes) - 16MB par défaut
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024
