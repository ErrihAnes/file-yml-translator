# translator_logic/translation_service.py
import time
from openai import OpenAI
from . import config  # Importation relative pour accéder aux configurations

# Initialisation du client OpenAI une seule fois lors du chargement du module
# Le script s'arrêtera si OPENAI_API_KEY n'est pas défini dans config.py
client = OpenAI(api_key=config.OPENAI_API_KEY)

# Cache de traduction au niveau du module pour persister entre les appels pour différentes langues
# si une même chaîne (source, cible) est demandée plusieurs fois (peu probable ici mais bonne pratique)
translation_cache = {}  # Format: {("texte_original", "code_langue_cible"): "texte_traduit"}


def translate_text_via_api(text_to_translate, target_lang_code, target_lang_name_for_prompt):
    """
    Traduit un texte en utilisant l'API OpenAI.
    Gère les erreurs, les tentatives, et utilise le cache du module.
    """
    # Ne pas traduire les chaînes vides ou constituées uniquement d'espaces
    if not text_to_translate.strip():
        return text_to_translate

    cache_key = (text_to_translate, target_lang_code)
    if cache_key in translation_cache:
        print(f"    CACHE HIT pour '{text_to_translate[:40]}...' -> '{target_lang_code}'")
        return translation_cache[cache_key]

    # Prompt système amélioré pour insister sur la préservation des placeholders et du Markdown
    system_prompt_message = (
        f"You are a highly skilled professional translation assistant. Your task is to translate "
        f"the user's text from {config.SOURCE_LANGUAGE_CODE} to {target_lang_name_for_prompt}. "
        f"CRITICAL INSTRUCTIONS: "
        f"1. PRESERVE ALL PLACEHOLDERS: Placeholders like {{example}}, {{user_name}}, "
        f"<t:{{timestamp}}:R>, etc., MUST be kept EXACTLY as they are in the original text. Do NOT translate them. "
        f"2. PRESERVE MARKDOWN: Markdown formatting such as ``code``, `code`, **bold**, *italic*, _underline_, "
        f"or [link](url) MUST be preserved. Do NOT alter it. "
        f"3. ACCURATE TRANSLATION: Provide an accurate and natural-sounding translation of the non-placeholder text. "
        f"4. OUTPUT FORMAT: Return ONLY the translated text. No explanations, no apologies, no additional text, "
        f"and no surrounding quotes unless they were part of the original string being translated."
    )

    user_content_message = text_to_translate

    for attempt in range(config.OPENAI_MAX_RETRIES):
        try:
            print(
                f"    Traduction API (tentative {attempt + 1}/{config.OPENAI_MAX_RETRIES}): '{text_to_translate[:60]}...' vers {target_lang_name_for_prompt}")

            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt_message},
                    {"role": "user", "content": user_content_message}
                ],
                temperature=config.OPENAI_TEMPERATURE,
                max_tokens=int(len(text_to_translate.encode('utf-8')) * 2.5 + 150),
                # Estimer en octets pour plus de précision avec unicode
                top_p=1.0,  # Valeurs par défaut généralement bonnes pour la traduction
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            translated_text = response.choices[0].message.content.strip()

            # Nettoyage simple si l'API ajoute des guillemets non désirés
            if translated_text.startswith('"') and translated_text.endswith('"') and not text_to_translate.startswith(
                    '"'):
                translated_text = translated_text[1:-1]
            if translated_text.startswith("'") and translated_text.endswith("'") and not text_to_translate.startswith(
                    "'"):
                translated_text = translated_text[1:-1]

            translation_cache[cache_key] = translated_text  # Mettre en cache le succès
            print(f"      -> SUCCÈS: '{translated_text[:60]}...'")
            return translated_text

        except Exception as e:
            print(
                f"      ERREUR API lors de la traduction de '{text_to_translate[:40]}...' vers {target_lang_name_for_prompt}: {e}")
            if attempt < config.OPENAI_MAX_RETRIES - 1:
                actual_delay = config.OPENAI_RETRY_DELAY_SECONDS * (attempt + 1)  # Backoff linéaire simple
                print(f"        Nouvelle tentative dans {actual_delay} secondes...")
                time.sleep(actual_delay)
            else:
                print(
                    f"      ÉCHEC FINAL de la traduction pour '{text_to_translate[:40]}...' après {config.OPENAI_MAX_RETRIES} tentatives.")
                return text_to_translate  # Retourner le texte original en cas d'échec final de toutes les tentatives

    # Ce point ne devrait être atteint que si OPENAI_MAX_RETRIES est 0, ce qui n'est pas recommandé.
    return text_to_translate

