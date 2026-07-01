# Steam-family-library-and-wishlist-comparator
Ce script Python permet de comparer votre liste de souhaits Steam avec les bibliothèques de jeux de votre famille.

Fusion des bibliothèques : Récupère automatiquement les jeux possédés par plusieurs utilisateurs via leurs SteamID64.

Analyse de Wishlist : Compare votre liste de souhaits avec l'ensemble des bibliothèques agrégées.

Exportation : Génère un fichier texte (resultats_wishlist_famille.txt) listant les jeux trouvés avec leur lien direct vers le magasin Steam.

Configuration :
Ouvrez le fichier et modifiez les variables suivantes :

API_KEY : Remplacez par votre clé API Steam.

STEAM_IDS : Remplacez par les SteamID64 des membres de votre famille. Le premier ID doit être le vôtre (celui dont on analyse la liste de souhaits).
