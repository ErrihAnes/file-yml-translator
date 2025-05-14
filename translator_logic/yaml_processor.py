import os

import yaml

def extract_text_values_recursive(data):
    """
    Extrait récursivement toutes les valeurs de type chaîne de caractères
    d'une structure de données imbriquée (dictionnaires et listes).
    Retourne un SET de chaînes uniques pour éviter les traductions redondantes.
    Toutes les chaînes sont extraites, y compris celles des clés 'name'.
    """
    strings_to_translate = set()
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                strings_to_translate.add(value)
            elif isinstance(value, (dict, list)):
                strings_to_translate.update(extract_text_values_recursive(value))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                strings_to_translate.add(item)
            elif isinstance(item, (dict, list)):
                strings_to_translate.update(extract_text_values_recursive(item))
    return strings_to_translate

def reconstruct_yaml_with_translations(original_data, translations_map):
    """
    Reconstruit récursivement la structure YAML avec les valeurs traduites.
    `translations_map` est un dictionnaire: {"original_text": "translated_text"}
    """
    if isinstance(original_data, dict):
        new_dict = {}
        for key, value in original_data.items():
            if isinstance(value, str):
                new_dict[key] = translations_map.get(value, value) # Utilise la traduction ou l'original si échec
            elif isinstance(value, (dict, list)):
                new_dict[key] = reconstruct_yaml_with_translations(value, translations_map)
            else:
                new_dict[key] = value # Conserve les nombres, booléens, etc.
        return new_dict
    elif isinstance(original_data, list):
        new_list = []
        for item in original_data:
            if isinstance(item, str):
                new_list.append(translations_map.get(item, item))
            elif isinstance(item, (dict, list)):
                new_list.append(reconstruct_yaml_with_translations(item, translations_map))
            else:
                new_list.append(item)
        return new_list
    return original_data

def load_yaml_file(file_path):
    """Charge un fichier YAML et retourne son contenu."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ERREUR CRITIQUE : Le fichier source '{file_path}' n'a pas été trouvé.")
        raise
    except yaml.YAMLError as e:
        print(f"ERREUR CRITIQUE : Erreur de syntaxe YAML dans '{file_path}': {e}")
        raise
    except Exception as e:
        print(f"ERREUR CRITIQUE : Une erreur inattendue est survenue lors du chargement de '{file_path}': {e}")
        raise

def save_yaml_file(data, file_path):
    """Sauvegarde des données dans un fichier YAML."""
    try:
        # S'assurer que le dossier parent existe
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, indent=2, width=1000)
        print(f"  Fichier traduit sauvegardé avec succès : '{file_path}'")
    except Exception as e:
        print(f"ERREUR : Échec de l'écriture du fichier YAML '{file_path}': {e}")
        # Ne pas lever d'exception ici pour permettre au script de continuer avec d'autres langues

