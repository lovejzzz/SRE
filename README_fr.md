[English](README.md) · [简体中文](README_zh.md) · [日本語](README_ja.md) · [Español](README_es.md) · [Français](README_fr.md) · [Deutsch](README_de.md) · [Português (Brasil)](README_pt-BR.md)

# SRE — Software Resynthesis Engine

[![Tests](https://github.com/lovejzzz/SRE/actions/workflows/test.yml/badge.svg)](https://github.com/lovejzzz/SRE/actions/workflows/test.yml)

**Indiquez le logiciel à reconstruire, la plateforme cible et les améliorations souhaitées.**

SRE est une skill pour agents qui étudient un logiciel existant et créent son successeur : conserver les comportements, les adapter à une autre plateforme et ajouter ou améliorer des fonctions. L’ambition couvre jeux, applications de bureau, CLI, Web et mobile. La faisabilité dépend des preuves accessibles, des dépendances et de la plateforme cible.

**v0.2 : une skill avec des outils exécutables de recherche et de validation.** L’agent hôte mène l’enquête et écrit le code. Il ne s’agit pas d’une garantie de reproduction intégrale de tout logiciel en un clic.

## Installation

Il faut un hôte prenant en charge les skills locales et **Python 3.10+**, sans dépendance Python tierce. REA est facultatif et n’est pas installé automatiquement.

```bash
git clone https://github.com/lovejzzz/SRE.git
python3 SRE/scripts/install.py
```

L’installateur utilise `$CODEX_HOME/skills` ou `~/.codex/skills` et refuse d’écraser une installation existante. Utilisez `--skills-dir /path/to/skills` pour changer le dossier. Préservez vos modifications lors des mises à jour, puis rechargez la skill dans l’hôte.

> Utilise $software-resynthesis pour étudier cette application de bureau et la reconstruire comme application Web hors ligne. Conserve le traitement des documents, ajoute des opérations par lots et compare le résultat à l’original. Livre un premier jalon testé sans perdre le périmètre complet demandé.

## Capacités disponibles

- Inventaires issus de plusieurs sources, correspondance avec les fonctions, dépendances, détection des omissions et références versionnées.
- Hypothèses concurrentes, prédictions, classement des expériences discriminantes et détection des contradictions.
- Exécution explicite d’adaptateurs avec dossier dédié, contrat de réinitialisation/action/observation/finalisation, empreintes, journaux et délai maximal.
- Erreurs d’images normalisées, conservation sémantique après sauvegarde et réouverture, traces d’interaction et budgets de performance liés au matériel et à la charge.
- Acceptation exigeant à la fois des preuves de comportement et un audit de recherche. Les preuves périmées et questions bloquantes empêchent la validation.

REA peut fournir l’analyse ; SRE relie la recherche aux spécifications, à l’implémentation et à l’acceptation. Aucun client REA n’est intégré et aucune supériorité mesurée sur REA n’est revendiquée.

## Exemple exécutable

```bash
cd SRE
python3 -m unittest discover -s tests -v
python3 examples/posix-path/run.py --workspace work/posix-run-1
```

L’exemple exécute réellement `posixpath.normpath` en Python et une implémentation JavaScript indépendante sur **417 entrées**. Il résout une question à partir d’observations et détecte une erreur volontaire. Node.js 18+ est requis ; le dossier de sortie doit être nouveau. Ce n’est pas une évaluation indépendante de reconstruction autonome d’applications complètes.

## Commandes et limites

`sre.py` expose `init`, `fingerprint`, `seal`, `audit`, `plan`, `run-adapter`, `compare`, `domain-check`, `check`. Consultez `--help`. Les sorties ne sont pas écrasées. Codes : 0 succès, 1 comparaison/acceptation/exécution non validée, 2 erreur d’entrée ou d’exécution. Les espaces v0.1 doivent recevoir de véritables relevés de découverte et une référence figée avant de réussir `check`.

SRE ne prouve ni l’exhaustivité des fonctions découvertes ni l’authenticité des expériences. Un jalon n’est pas un produit complet. Il n’inclut ni robot d’exploration universel, ni ordonnanceur permanent, ni adaptateur d’exécution PZ/Photoshop. L’agent recueille les sources et conçoit les hypothèses. Les adaptateurs utilisent les permissions de l’hôte et ne sont pas isolés dans un bac à sable. Les validateurs lisent du JSON normalisé ; analyse PSD, décodage d’images, opérations GUI et mesures matérielles exigent des adaptateurs spécifiques. Les implémentations serveur inaccessibles ne peuvent pas être récupérées, et toute charge ne peut pas être garantie sur toute plateforme.

Les évaluations indépendantes d’agents n’ont pas été réalisées. Gardez les échantillons privés, identifiants et données personnelles hors du dépôt public ; respectez les licences du code réutilisé.

[Recherche](skills/software-resynthesis/references/research-protocol.md) · [Adaptateurs](skills/software-resynthesis/references/adapters.md) · [Validation par domaine](skills/software-resynthesis/references/domain-validation.md) · [Évaluation](evals/behavioral.md)

Les rapports de défauts reproductibles et anonymisés, avec versions, entrées, résultats attendus/réels et preuves, ainsi que les améliorations de traduction, sont bienvenus. Les protocoles techniques détaillés sont actuellement en anglais.
