import os
import pymongo
from dotenv import load_dotenv
from github import Github

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Connexion à MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "educational_chatbot")

if not MONGODB_URI or not MONGO_DB_NAME:
    raise ValueError("MONGODB_URI ou MONGO_DB_NAME manquant dans le fichier .env")

client = pymongo.MongoClient(MONGODB_URI)
db = client[MONGO_DB_NAME]
courses_collection = db["courses"]

# Connexion à GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # Doit être de la forme "utilisateur/repo"

github = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None
