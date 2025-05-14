# run_translator.py
import os
import time
from translator_logic import config  # Importe nos configurations centralisées
from translator_logic.yaml_processor import (
    load_yaml_file,
    extract_text_values_recursive,
    reconstruct_yaml_with_translations,
    save_yaml_file
)
from translator_logic.translation_service import translate_text_via_api


def run_main_translation_process():
    """
    Fonction principale pour orchestrer le processus de traduction de YAML.
    """
    print("=" * 50)
    print("DÉMARRAGE DU PROCESSUS DE TRADUCTION YAML")
    print("=" * 50)

    # 1. Charger le fichier YML source
    try:
        original_yaml_data = load_yaml_file(config.SOURCE_FILE_PATH)
        if original_yaml_data is None:  # Si load_yaml_file a échoué et levé une exception attrapée plus haut
            print("Arrêt du processus en raison d'une erreur de chargement du fichier source.")
            return
        print(f"Fichier source '{config.SOURCE_FILE_PATH}' chargé avec succès.")
    except Exception:
        # L'erreur est déjà loguée par load_yaml_file, le programme s'arrêtera car l'exception est levée
        return

    # 2. Extraire toutes les valeurs textuelles uniques à traduire
    #   Le tri par longueur (plus longues d'abord) est une petite heuristique qui peut parfois aider
    #   l'IA en lui donnant plus de contexte au début, mais son impact est variable.
    all_texts_to_translate_set = extract_text_values_recursive(original_yaml_data)
    all_texts_to_translate_list = sorted(list(all_texts_to_translate_set), key=len, reverse=True)

    if not all_texts_to_translate_list:
        print("Aucune valeur textuelle à traduire n'a été trouvée dans le fichier YAML.")
        print("Processus terminé.")
        return
    print(f"{len(all_texts_to_translate_list)} chaînes de texte uniques identifiées pour la traduction.\n")

    # 3. Traduire pour chaque langue cible définie dans la configuration
    total_languages = len(config.TARGET_LANGUAGES)
    for lang_idx, (lang_code, lang_name_for_prompt) in enumerate(config.TARGET_LANGUAGES.items()):
        print(
            f"\n--- TRADUCTION EN COURS POUR : {lang_name_for_prompt} ({lang_code}) [{lang_idx + 1}/{total_languages}] ---")

        current_language_translations_map = {}  # Stocke: {"original_text": "translated_text"} pour la langue actuelle

        num_strings_for_lang = len(all_texts_to_translate_list)
        for str_idx, text_to_translate in enumerate(all_texts_to_translate_list):
            print(f"  Traitement de la chaîne {str_idx + 1}/{num_strings_for_lang} pour {lang_code}:")

            translated_text_result = translate_text_via_api(
                text_to_translate,
                lang_code,
                lang_name_for_prompt  # Le nom de langue descriptif pour le prompt
            )
            current_language_translations_map[text_to_translate] = translated_text_result

            # Pause configurée entre les requêtes API pour éviter le "rate limiting"
            if config.API_REQUEST_DELAY_SECONDS > 0:
                time.sleep(config.API_REQUEST_DELAY_SECONDS)

        # 4. Reconstruire la structure YAML avec les traductions pour la langue actuelle
        print(f"\n  Reconstruction du fichier YAML pour {lang_name_for_prompt} ({lang_code})...")
        translated_yaml_data_for_lang = reconstruct_yaml_with_translations(
            original_yaml_data,
            current_language_translations_map
        )

        # 5. Sauvegarder le nouveau fichier YML traduit
        source_file_basename = os.path.splitext(os.path.basename(config.SOURCE_FILE_PATH))[0]
        output_filename = os.path.join(config.OUTPUT_DIR_PATH, f"{source_file_basename}_{lang_code}.yml")

        save_yaml_file(translated_yaml_data_for_lang, output_filename)
        # L'erreur de sauvegarde est gérée dans save_yaml_file, le script continuera

    print("\n" + "=" * 50)
    print("PROCESSUS DE TRADUCTION TERMINÉ !")
    print(f"Les fichiers traduits ont été sauvegardés dans : '{config.OUTPUT_DIR_PATH}'")
    print("=" * 50)


if __name__ == "__main__":
    # Créer le dossier de sortie au début si nécessaire
    if not os.path.exists(config.OUTPUT_DIR_PATH):
        try:
            os.makedirs(config.OUTPUT_DIR_PATH)
            print(f"Dossier de sortie '{config.OUTPUT_DIR_PATH}' créé.")
        except OSError as e:
            print(f"ERREUR CRITIQUE : Impossible de créer le dossier de sortie '{config.OUTPUT_DIR_PATH}': {e}")
            # Quitter si le dossier de sortie ne peut pas être créé
            exit()  # ou sys.exit(1) après import sys

    run_main_translation_process()