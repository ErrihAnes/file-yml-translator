import os
import sys
from dotenv import load_dotenv
# Assurer l'accès à langues.py s'il est à la racine du projet
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)
try:
    from langues import language_codes
except ImportError:
    print("AVERTISSEMENT: Le fichier 'langues.py' n'a pas été trouvé à la racine du projet.")
    print("Utilisation d'une liste de langues par défaut pour la démonstration.")
    language_codes = ["fr", "de", "es-ES"] # Liste de secours

load_dotenv(dotenv_path=os.path.join(project_root, '.env')) # S'assurer de charger

# --- Clés API ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SOURCE_FILE_PATH = os.path.join(project_root, "message.yml")
OUTPUT_DIR_PATH = os.path.join(project_root, "translated_files")


SOURCE_LANGUAGE_CODE = "en"
TARGET_LANGUAGES = {}
try:
    import pycountry
    PYCOUNTRY_AVAILABLE = True
except ImportError:
    PYCOUNTRY_AVAILABLE = False
    print("AVERTISSEMENT: La bibliothèque 'pycountry' n'est pas installée. Les noms de langue pour les prompts seront moins précis.")
    print("Pour une meilleure qualité, installez-la avec: pip install pycountry")


for code in language_codes:
    lang_name_for_prompt = code # Fallback initial
    if PYCOUNTRY_AVAILABLE:
        try:
            # Tente de trouver la langue. Pour les codes comme 'zh-CN', on prend 'zh'.
            lang_obj = pycountry.languages.get(alpha_2=code.split('-')[0])
            if lang_obj:
                lang_name_for_prompt = lang_obj.name
                if "-" in code: # Ajoute la spécificité régionale si présente
                    lang_name_for_prompt += f" ({code.split('-', 1)[1]})" # ex: English (US)
        except Exception: # pycountry peut ne pas trouver tous les codes ou variantes
            pass # Garde le code comme nom si pycountry échoue
    else: # Si pycountry n'est pas là, quelques cas courants manuels
        common_names = {
            "en-US": "English (US)", "en-GB": "English (UK)", "zh-CN": "Chinese (Simplified)",
            "zh-TW": "Chinese (Traditional)", "pt-BR": "Portuguese (Brazil)",
            "es-ES": "Spanish (Spain)", "es-419": "Spanish (Latin America)",
            "fr": "French", "de": "German", "it": "Italian", "ja": "Japanese"
        }
        lang_name_for_prompt = common_names.get(code, code.upper()) # Fallback au code en majuscules

    TARGET_LANGUAGES[code] = lang_name_for_prompt

# --- Paramètres de l'API OpenAI ---
OPENAI_MODEL = "gpt-3.5-turbo"  # Ou "gpt-4" si vous avez accès et préférez une meilleure qualité (plus cher)
OPENAI_TEMPERATURE = 0.2        # Plus bas pour des traductions plus littérales
OPENAI_MAX_RETRIES = 3          # Nombre de tentatives en cas d'échec de l'API
OPENAI_RETRY_DELAY_SECONDS = 5  # Délai initial avant une nouvelle tentative
API_REQUEST_DELAY_SECONDS = 0.6 # Délai entre les requêtes API pour éviter le rate limiting (0.5-1s est souvent bien)

# --- Validation de la configuration essentielle ---
if not OPENAI_API_KEY:
    raise ValueError(
        "La variable d'environnement OPENAI_API_KEY n'est pas définie. "
        "Veuillez la configurer dans votre fichier .env à la racine du projet."
    )

print("Configuration chargée :")
print(f"  Fichier source : {SOURCE_FILE_PATH}")
print(f"  Dossier de sortie : {OUTPUT_DIR_PATH}")
print(f"  Langue source : {SOURCE_LANGUAGE_CODE}")
print("  Langues cibles et noms pour le prompt :")
for lc, ln in TARGET_LANGUAGES.items():
    print(f"    - {lc}: {ln}")
print("-" * 30)