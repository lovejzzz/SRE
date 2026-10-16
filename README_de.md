[English](README.md) · [简体中文](README_zh.md) · [日本語](README_ja.md) · [Español](README_es.md) · [Français](README_fr.md) · [Deutsch](README_de.md) · [Português (Brasil)](README_pt-BR.md)

# SRE — Software Resynthesis Engine

[![Tests](https://github.com/lovejzzz/SRE/actions/workflows/test.yml/badge.svg)](https://github.com/lovejzzz/SRE/actions/workflows/test.yml)

**Nenne die Software, die Zielplattform und die gewünschten Verbesserungen.**

SRE ist ein Skill für Agenten, die vorhandene Software untersuchen und einen Nachfolger entwickeln: Verhalten bewahren, an andere Plattformen anpassen und Funktionen ergänzen oder verbessern. Das Ziel umfasst Spiele, Desktop-Anwendungen, CLI-Werkzeuge sowie Web- und Mobilsoftware. Die Machbarkeit hängt von verfügbaren Belegen, Abhängigkeiten und der Zielplattform ab.

**v0.2: ein Skill mit ausführbaren Forschungs- und Prüfwerkzeugen.** Recherche und Programmierung übernimmt der ausführende Agent. Eine vollständige Ein-Klick-Rekonstruktion beliebiger Software wird nicht garantiert.

## Installation

Voraussetzung sind ein Host mit Unterstützung für lokale Skills und **Python 3.10+**, ohne zusätzliche Python-Pakete. [REA](https://github.com/morluto/rea) ist optional und wird nicht automatisch installiert.

```bash
git clone https://github.com/lovejzzz/SRE.git
python3 SRE/scripts/install.py
```

Das Installationsprogramm verwendet `$CODEX_HOME/skills` oder `~/.codex/skills` und überschreibt keine bestehende Installation. Mit `--skills-dir /path/to/skills` lässt sich das Ziel ändern. Lokale Änderungen beim Aktualisieren erhalten und den Skill im Host neu laden.

> Nutze $software-resynthesis, um diese Desktop-Anwendung zu untersuchen und als offlinefähige Webanwendung neu zu entwickeln. Bewahre den Dokumentenablauf, ergänze Stapelverarbeitung und prüfe gegen das Original. Liefere zunächst einen getesteten Meilenstein, ohne den vollständigen Auftrag zu verkürzen.

## Implementierte Fähigkeiten

- Funktionsinventare aus mehreren Quellen, Zuordnungen, Abhängigkeiten, Erkennung fehlender Einträge und versionierte Ausgangsstände.
- Konkurrierende Hypothesen, Vorhersagen, Priorisierung unterscheidender Experimente und Widerspruchserkennung.
- Explizite Adapterausführung mit eigenem Arbeitsverzeichnis, Reset/Aktion/Beobachtung/Abschluss-Vertrag, Hashes, Protokollen und Zeitlimit.
- Fehlermaße für normalisierte Bilder, semantische Prüfungen nach Speichern und erneutem Öffnen, Interaktionsspuren sowie geräte- und lastbezogene Leistungsbudgets.
- Abnahme nur mit Verhaltensbelegen und Forschungsaudit. Veraltete Belege und offene blockierende Fragen verhindern die Freigabe.

REA kann Analysefähigkeiten bereitstellen. SRE verbindet Forschung mit Spezifikation, Implementierung und Abnahme. Ein REA-Client ist nicht enthalten; eine gemessene Überlegenheit gegenüber REA wird nicht behauptet.

## Ausführbares Beispiel

```bash
cd SRE
python3 -m unittest discover -s tests -v
python3 examples/posix-path/run.py --workspace work/posix-run-1
```

Das Beispiel führt Pythons `posixpath.normpath` und eine unabhängige JavaScript-Implementierung mit **417 Eingaben** aus. Beobachtungen beantworten eine Forschungsfrage; ein absichtlich eingebauter Fehler wird erkannt. Node.js 18+ und ein noch nicht vorhandenes Ausgabeverzeichnis sind erforderlich. Dies ist keine unabhängige Bewertung autonomer Rekonstruktion vollständiger Anwendungen.

## Befehle und Grenzen

`sre.py`: `init`, `fingerprint`, `seal`, `audit`, `plan`, `run-adapter`, `compare`, `domain-check`, `check`. Argumente stehen unter `--help`. Ausgaben werden nicht überschrieben. Rückgabecodes: 0 Erfolg, 1 Vergleich/Abnahme/Lauf fehlgeschlagen, 2 Eingabe- oder Ausführungsfehler. Arbeitsbereiche aus v0.1 brauchen echte Erhebungsdaten und einen festgeschriebenen Forschungsstand für `check`.

SRE beweist weder die Vollständigkeit entdeckter Funktionen noch die Echtheit von Experimenten. Ein Meilenstein ist kein fertiges Gesamtprodukt. Es gibt keinen universellen Crawler, dauerhaften Hintergrundplaner oder PZ/Photoshop-Laufzeitadapter. Quellen und Hypothesen werden vom Agenten erarbeitet. Adapter laufen mit Host-Rechten und sind keine Sandbox. Validatoren verwenden normalisiertes JSON; PSD-Analyse, Bilddekodierung, GUI-Bedienung und Gerätemessung benötigen passende Adapter. Unzugängliche Serverimplementierungen können nicht wiederhergestellt werden; beliebige Lasten sind nicht auf jeder Plattform realisierbar.

Unabhängige Agentenbewertungen wurden noch nicht durchgeführt. Private Beispiele, Zugangsdaten und persönliche Daten gehören nicht ins öffentliche Repository; Lizenzen wiederverwendeten Codes sind einzuhalten.

[Forschungsprotokoll](skills/software-resynthesis/references/research-protocol.md) · [Adapter](skills/software-resynthesis/references/adapters.md) · [Fachspezifische Prüfung](skills/software-resynthesis/references/domain-validation.md) · [Bewertung](evals/behavioral.md)

Reproduzierbare, bereinigte Fehlerberichte mit Versionen, Eingaben, Soll-/Ist-Verhalten und Belegen sowie Übersetzungsverbesserungen sind willkommen. Detaillierte technische Protokolle liegen derzeit auf Englisch vor.

Integritätsupdate: Zielvalidierungen und Forschungsbeobachtungen benötigen SHA-256. Siehe [Migration und Grenzen](skills/software-resynthesis/references/validation.md#recorded-evidence-integrity) und [Änderungsprotokoll](CHANGELOG.md).

Prozessprotokoll: `sre.py record` / `report` speichern Schritte, Fehler, Korrekturen und Prüfsummen der Nachweise. Siehe [Protokollformat](skills/software-resynthesis/references/work-journal.md) und den laufenden [Project-Zomboid-Fall](docs/project-zomboid/PROCESS.md), der noch unvollständig ist und keine Übereinstimmung bestätigt.
