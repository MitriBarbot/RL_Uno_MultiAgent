1. Préparer le ReplayReader

10 min

[ ] Créer visualization/replay_reader.py
[ ] Créer class ReplayReader
[ ] Prévoir __init__(replay_path)
[ ] Charger le JSON avec json.load()
[ ] Stocker setup, turns et result


2. Reconstruire l'état initial

20 min

[ ] Créer reset() pour revenir au début du replay
[ ] Copier les mains initiales avec deepcopy()
[ ] Initialiser la carte visible et la couleur active
[ ] Initialiser le sens de jeu
[ ] Initialiser le joueur actif et le curseur du replay


3. Interpréter les événements

30 min

[ ] Créer apply_event(event)
[ ] PLAY : retirer une carte de la bonne main
[ ] DRAW : ajouter les cartes réellement piochées
[ ] COLOR_CHANGE : changer la couleur active
[ ] DIRECTION_CHANGE : changer le sens de jeu
[ ] PASS et SKIP : aucune modification des mains


4. Naviguer dans les tours

20 min

[ ] Créer next_turn()
[ ] Appliquer tous les événements du tour courant
[ ] Mettre à jour le joueur actif
[ ] Incrémenter le curseur
[ ] Détecter la fin du replay
[ ] Créer éventuellement previous_turn() via reset + relecture


5. Vérifier la reconstruction

20 min

[ ] Afficher les tailles des quatre mains après chaque tour
[ ] Vérifier que la carte jouée était présente dans la main
[ ] Vérifier qu'aucune main ne possède un nombre négatif de cartes
[ ] Comparer les mains finales à celles de UnoGame
[ ] Ajouter des tests pytest propres au ReplayReader


6. Préparer le moteur visuel

10 min

[ ] Créer get_state() pour exposer l'état reconstruit
[ ] Vérifier que get_state() ne renvoie pas de références modifiables
[ ] Faire un commit Git de cette première version