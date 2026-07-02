import requests
import time
import os

API_KEY = 'YOUR_STEAM_API_KEY'  # Remplacez par votre clé API Steam

# Mettez VOTRE SteamID64 en premier dans la liste, suivi de ceux de votre famille
MY_STEAM_ID = 'YOUR_STEAM_ID64' # Remplacez par votre SteamID64
STEAM_IDS = [MY_STEAM_ID, 'FAMILY_MEMBER_1_STEAM_ID64', 'FAMILY_MEMBER_2_STEAM_ID64'] # Remplacez par les SteamID64 de vos membres de famille

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
}

session = requests.Session()
session.headers.update(HEADERS)


def safe_get_json(url, retries=3, pause=3):
    """Fait une requête et renvoie du JSON, ou None si ça échoue vraiment."""
    backoff = 15

    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, timeout=10)
        except requests.RequestException as e:
            print(f"   Erreur réseau ({e}), tentative {attempt}/{retries}...")
            time.sleep(pause)
            continue

        if response.status_code == 429:
            print(f"   Trop de requêtes envoyées, pause de {backoff}s...")
            time.sleep(backoff)
            backoff = min(backoff * 2, 120)
            continue

        if response.status_code == 404:
            print("   Erreur HTTP 404 (route introuvable), abandon pour cette requête.")
            return None

        if response.status_code != 200:
            print(f"   Erreur HTTP {response.status_code}, tentative {attempt}/{retries}...")
            time.sleep(pause)
            continue

        try:
            return response.json()
        except ValueError:
            print(f"   Réponse non-JSON reçue, tentative {attempt}/{retries}...")
            time.sleep(pause)

    return None


def get_app_names():
    """Télécharge l'annuaire Steam pour traduire les AppID en vrais noms."""
    print("Téléchargement de la base de données des noms Steam...")
    app_names = {}
    last_appid = 0
    have_more = True

    while have_more:
        url = (
            "https://api.steampowered.com/IStoreService/GetAppList/v1/"
            f"?key={API_KEY}&include_games=true&include_dlc=true"
            f"&max_results=50000&last_appid={last_appid}"
        )
        data = safe_get_json(url, retries=3, pause=5)
        if not data or 'response' not in data:
            print("Impossible de charger l'annuaire (Plan B activé pour les noms).")
            return app_names

        apps = data['response'].get('apps', [])
        for app in apps:
            app_names[app['appid']] = app['name']

        have_more = data['response'].get('have_more_results', False)
        last_appid = data['response'].get('last_appid', 0)

    return app_names


def get_owned_games(steam_id):
    """Récupère les AppID des jeux possédés."""
    url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={API_KEY}&steamid={steam_id}&format=json"
    data = safe_get_json(url)
    if data and 'response' in data and 'games' in data['response']:
        return [game['appid'] for game in data['response']['games']]
    print(f"ID {steam_id} : aucun jeu trouvé ou profil privé.")
    return []


def get_wishlist(steam_id):
    """Récupère les AppID de la liste de souhaits via l'API officielle Steam."""
    url = f"https://api.steampowered.com/IWishlistService/GetWishlist/v1/?key={API_KEY}&steamid={steam_id}"
    data = safe_get_json(url)
    if data and 'response' in data and 'items' in data['response']:
        return [item['appid'] for item in data['response']['items']]
    return []


def get_name(appid, steam_app_names, cache):
    """Nom d'une appid : d'abord l'annuaire (gratuit), sinon appdetails (Plan B, coûteux).
    La pause de 3s n'est appliquée que si un vrai appel API a été nécessaire."""
    if appid in steam_app_names:
        return steam_app_names[appid]
    if appid in cache:
        return cache[appid]

    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    data = safe_get_json(url)
    time.sleep(3)  # pause uniquement ici, car c'est le seul cas qui tape l'API appdetails

    name = f"Jeu Inconnu ({appid})"
    if data and str(appid) in data and data[str(appid)].get('success'):
        name = data[str(appid)]['data']['name']
    cache[appid] = name
    return name


def main():
    # 1. Récupération de l'annuaire
    steam_app_names = get_app_names()
    name_cache = {}

    # 2. Fusion des bibliothèques
    all_owned_apps = set()
    print("\nRécupération des bibliothèques de la famille...")
    for steam_id in STEAM_IDS:
        all_owned_apps.update(get_owned_games(steam_id))

    print(f"Total des jeux/apps uniques trouvés dans la famille : {len(all_owned_apps)}")

    # 3. Récupération de la liste de souhaits
    mon_steam_id = STEAM_IDS[0]
    print("\nChargement de votre liste de souhaits...")
    ma_wishlist_appids = get_wishlist(mon_steam_id)
    print(f"Total des jeux dans la liste de souhaits : {len(ma_wishlist_appids)}")

    if len(ma_wishlist_appids) == 0:
        print("\nLa liste est vide. Assurez-vous que les 'Détails des jeux' sont bien en mode Public sur votre profil Steam.")
        return

    # 4. Croisement et exportation
    dossier_du_script = os.path.dirname(os.path.abspath(__file__))
    nom_fichier = os.path.join(dossier_du_script, "resultats_wishlist_famille.txt")

    with open(nom_fichier, "w", encoding="utf-8") as fichier:
        fichier.write("=== JEUX DE MA WISHLIST DÉJÀ POSSÉDÉS PAR LA FAMILLE ===\n\n")

        print("Analyse en cours...")
        trouves = 0
        for appid in ma_wishlist_appids:
            if appid in all_owned_apps:
                nom_jeu = get_name(appid, steam_app_names, name_cache)
                fichier.write(f"- {nom_jeu} (AppID: {appid})\n")
                fichier.write(f"   -> Voir sur le magasin : https://store.steampowered.com/app/{appid}\n\n")
                trouves += 1

        if trouves == 0:
            fichier.write("Aucun jeu de la liste de souhaits n'est possédé par la famille.\n")

    print(f"\nTerminé ! {trouves} jeu(x) trouvé(s) ! Résultats dans le fichier : {nom_fichier}")


if __name__ == "__main__":
    main()