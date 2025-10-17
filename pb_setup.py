#!/usr/bin/env python3
"""
PocketBase Project Setup Script
Automatise la création d'un projet PocketBase avec hooks TypeScript
"""

import os
import sys
import json
import subprocess
import urllib.request
import urllib.error
import platform
import shutil
import zipfile
from pathlib import Path


class PocketBaseSetup:
    def __init__(self, project_dir=None, pb_version=None, pb_port=None):
        self.project_dir = project_dir
        self.pb_version = pb_version
        self.pb_port = pb_port if pb_port is not None else 8090
        self.os_type = platform.system().lower()
        self.arch = platform.machine()

    def select_project_dir(self):
        """Demande à l'utilisateur dans quel dossier créer le projet (si non fourni)"""
        # Si déjà défini via arguments, valider et utiliser
        if self.project_dir:
            self.project_dir = Path(self.project_dir).expanduser().resolve()
            if not self.project_dir.exists():
                try:
                    self.project_dir.mkdir(parents=True, exist_ok=True)
                    print(f"📁 Dossier créé: {self.project_dir}\n")
                except Exception as e:
                    print(f"❌ Impossible de créer le dossier: {e}")
                    sys.exit(1)
            else:
                print(f"📁 Utilisation du dossier: {self.project_dir}\n")
            return

        # Sinon, demander à l'utilisateur
        print("📁 Emplacement du projet PocketBase\n")

        while True:
            path_input = input("Entrez le chemin du dossier (ou . pour le dossier courant): ").strip()

            if path_input == ".":
                self.project_dir = Path.cwd()
            else:
                self.project_dir = Path(path_input).expanduser().resolve()

            # Vérifier si le dossier existe
            if self.project_dir.exists():
                # Vérifier si le dossier est vide ou demander confirmation
                if list(self.project_dir.iterdir()):
                    confirm = input(f"⚠️  Le dossier {self.project_dir} n'est pas vide. Continuer? (y/n): ").strip().lower()
                    if confirm == 'y':
                        print(f"✅ Utilisation du dossier: {self.project_dir}\n")
                        return
                    else:
                        continue
                else:
                    print(f"✅ Utilisation du dossier: {self.project_dir}\n")
                    return
            else:
                # Créer le dossier
                try:
                    self.project_dir.mkdir(parents=True, exist_ok=True)
                    print(f"✅ Dossier créé: {self.project_dir}\n")
                    return
                except Exception as e:
                    print(f"❌ Impossible de créer le dossier: {e}")
                    continue

    def get_pocketbase_versions(self):
        """Récupère les versions disponibles de PocketBase depuis GitHub"""
        try:
            print("📡 Récupération des versions disponibles...")
            url = "https://api.github.com/repos/pocketbase/pocketbase/releases?per_page=30"

            # Retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'pb_setup/1.0')
                    req.add_header('Accept', 'application/vnd.github.v3+json')

                    with urllib.request.urlopen(req, timeout=15) as response:
                        # Lire le contenu avec gestion propre des chunks
                        content_length = response.headers.get('content-length')
                        data = response.read()

                        if not data:
                            raise Exception("Réponse vide du serveur")

                        releases = json.loads(data.decode('utf-8'))
                        versions = [r['tag_name'] for r in releases if not r['prerelease']]

                        if versions:
                            print(f"   ✅ {len(versions)} versions trouvées")
                            return versions[:15]  # Les 15 dernières versions
                        else:
                            raise Exception("Aucune version trouvée")

                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"   ⚠️  Tentative {attempt + 1} échouée: {str(e)[:50]}")
                        import time
                        time.sleep(1)  # Attendre avant de réessayer
                    else:
                        raise

        except Exception as e:
            print(f"⚠️  Impossible de récupérer les versions: {str(e)[:80]}")
            print("   Utilisation de versions par défaut...")
            # Versions par défaut récentes
            return ['v0.30.3', 'v0.30.2', 'v0.30.1', 'v0.30.0', 'v0.29.3', 'v0.29.2', 'v0.29.1', 'v0.29.0', 'v0.28.0']

    def select_port(self):
        """Demande à l'utilisateur de configurer le port (si non fourni)"""
        # Valider le port si déjà défini via arguments
        if self.pb_port != 8090 or hasattr(self, '_port_from_args'):
            if 1024 <= self.pb_port <= 65535:
                print(f"🔌 Port configuré: {self.pb_port}")
            else:
                print(f"⚠️  Le port doit être entre 1024 et 65535. Utilisation du port par défaut: 8090")
                self.pb_port = 8090
            return

        # Sinon, demander à l'utilisateur
        print("\n🔌 Configuration du port\n")
        print(f"   Port par défaut: {self.pb_port}")

        port_input = input("   Appuyez sur Entrée pour conserver le port par défaut ou tapez un nouveau port: ").strip()

        if port_input:
            try:
                port = int(port_input)
                if 1024 <= port <= 65535:
                    self.pb_port = port
                    print(f"✅ Port configuré: {self.pb_port}")
                else:
                    print(f"⚠️  Le port doit être entre 1024 et 65535. Utilisation du port par défaut: {self.pb_port}")
            except ValueError:
                print(f"⚠️  Port invalide. Utilisation du port par défaut: {self.pb_port}")
        else:
            print(f"✅ Port par défaut utilisé: {self.pb_port}")

    def select_version(self):
        """Demande à l'utilisateur de sélectionner une version (si non fournie)"""
        # Si version déjà définie via arguments, l'utiliser
        if self.pb_version:
            if self.pb_version.startswith('v') and self.pb_version[1:].replace('.', '').isdigit():
                print(f"📦 Version sélectionnée: {self.pb_version}")
                return
            else:
                print(f"⚠️  Version invalide: {self.pb_version}. Récupération depuis GitHub...")

        # Sinon, demander à l'utilisateur
        versions = self.get_pocketbase_versions()
        if not versions:
            print("⚠️  Impossible de récupérer les versions. Utilisation de 'latest'")
            self.pb_version = "latest"
            return

        print("\n📦 Versions disponibles:")
        for i, version in enumerate(versions, 1):
            print(f"  {i}. {version}")

        while True:
            try:
                choice = input(f"\nSélectionnez une version (1-{len(versions)}): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(versions):
                    self.pb_version = versions[idx]
                    print(f"✅ Version sélectionnée: {self.pb_version}")
                    return
                else:
                    print(f"❌ Veuillez entrer un numéro entre 1 et {len(versions)}")
            except ValueError:
                print("❌ Entrée invalide")

    def get_pocketbase_download_url(self):
        """Construit l'URL de téléchargement PocketBase"""
        # Mapping OS/Architecture vers noms PocketBase
        os_map = {
            'linux': 'linux',
            'darwin': 'darwin',
            'windows': 'windows'
        }

        arch_map = {
            'x86_64': 'amd64',
            'arm64': 'arm64',
            'amd64': 'amd64'
        }

        os_name = os_map.get(self.os_type, 'linux')
        arch_name = arch_map.get(self.arch, 'amd64')

        # Extraire le numéro de version (v0.30.3 -> 0.30.3)
        version_num = self.pb_version.lstrip('v')

        filename = f"pocketbase_{version_num}_{os_name}_{arch_name}.zip"
        url = f"https://github.com/pocketbase/pocketbase/releases/download/{self.pb_version}/{filename}"

        return url, filename

    def get_cache_dir(self):
        """Récupère ou crée le répertoire cache"""
        cache_dir = Path.home() / '.pb_cache'
        cache_dir.mkdir(exist_ok=True)
        return cache_dir

    def download_pocketbase(self):
        """Télécharge et extrait le binaire PocketBase avec cache"""
        url, filename = self.get_pocketbase_download_url()
        cache_dir = self.get_cache_dir()
        cached_zip = cache_dir / filename

        print(f"\n⬇️  PocketBase ({self.os_type}_{self.arch})...")

        # Vérifier le cache
        if cached_zip.exists():
            print(f"   📦 Trouvé en cache: {cached_zip}")
            zip_path = cached_zip
        else:
            print(f"   URL: {url}")
            print(f"   (Téléchargement sera mis en cache dans {cache_dir})")

            try:
                # Télécharger dans le cache
                def download_progress(block_num, block_size, total_size):
                    downloaded = block_num * block_size
                    percent = min(100, int(downloaded / total_size * 100))
                    print(f"   Progression: {percent}%", end='\r')

                urllib.request.urlretrieve(url, cached_zip, download_progress)
                print(f"\n✅ PocketBase téléchargé et sauvegardé en cache")
            except Exception as e:
                print(f"❌ Erreur de téléchargement: {e}")
                return False

            zip_path = cached_zip

        # Extraire le fichier ZIP dans le projet
        try:
            print("📦 Extraction du fichier...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.project_dir)

            # Rendre le binaire exécutable (Linux/macOS)
            if self.os_type in ['linux', 'darwin']:
                pocketbase_bin = self.project_dir / 'pocketbase'
                if pocketbase_bin.exists():
                    os.chmod(pocketbase_bin, 0o755)
                    print(f"✅ Binaire rendu exécutable: pocketbase")

            print("✅ Extraction terminée")
            return True
        except Exception as e:
            print(f"❌ Erreur d'extraction: {e}")
            return False

    def create_folder_structure(self):
        """Crée la structure des dossiers du projet"""
        print("\n📁 Création de la structure des dossiers...")

        folders = [
            'pb_hooks',
            'pb_hooks_ts',
            'pb_migration',
            'pb_public',
            'pb_data'
        ]

        for folder in folders:
            path = self.project_dir / folder
            path.mkdir(exist_ok=True)
            print(f"  ✅ {folder}/")

            # Créer un fichier .gitkeep dans pb_data pour le conserver dans git
            if folder == 'pb_data':
                gitkeep_file = path / '.gitkeep'
                gitkeep_file.touch()

        print("✅ Structure des dossiers créée")

    def initialize_typescript_project(self):
        """Initialise le projet TypeScript dans pb_hooks_ts/"""
        print("\n🔧 Initialisation du projet TypeScript...")

        ts_dir = self.project_dir / 'pb_hooks_ts'

        # Créer les sous-dossiers
        (ts_dir / 'src' / 'entries').mkdir(parents=True, exist_ok=True)
        (ts_dir / 'src' / 'types').mkdir(parents=True, exist_ok=True)
        (ts_dir / 'src' / 'lib').mkdir(parents=True, exist_ok=True)

        # Créer package.json
        package_json = {
            "name": "pb_hooks",
            "version": "1.0.0",
            "description": "PocketBase TypeScript Hooks",
            "scripts": {
                "build": "tsup src/entries/**/*.ts -d ../pb_hooks",
                "dev": "chokidar './src/entries/**' -c 'npm run build' --initial"
            },
            "devDependencies": {
                "typescript": "^5.2.2",
                "tsup": "^7.2.0",
                "chokidar-cli": "^3.0.0",
                "@swc/core": "^1.3.0"
            }
        }

        with open(ts_dir / 'package.json', 'w') as f:
            json.dump(package_json, f, indent=2)
        print("  ✅ package.json créé")

        # Créer tsup.config.ts
        tsup_config = """import { defineConfig } from 'tsup'

export default defineConfig({
  entry: ['./src/entries/**/*.ts'],
  format: ['cjs'],
  outDir: '../pb_hooks',
  splitting: false,
  sourcemap: true,
  clean: true,
  bundle: false,
  shims: false,
})
"""

        with open(ts_dir / 'tsup.config.ts', 'w') as f:
            f.write(tsup_config)
        print("  ✅ tsup.config.ts créé")

        # Créer tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "ES5",
                "module": "ES2015",
                "lib": ["ES5"],
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "forceConsistentCasingInFileNames": True,
                "resolveJsonModule": True,
                "sourceMap": True,
                "allowJs": True,
                "checkJs": False,
                "noUncheckedIndexedAccess": True,
                "strictNullChecks": True,
                "noUnusedParameters": True,
                "noEmit": True
            },
            "include": ["src/**/*"],
            "exclude": ["node_modules"]
        }

        with open(ts_dir / 'tsconfig.json', 'w') as f:
            json.dump(tsconfig, f, indent=2)
        print("  ✅ tsconfig.json créé")

        print("✅ Projet TypeScript initialisé")

    def create_hook_template(self):
        """Crée un template de hook TypeScript"""
        print("\n📝 Création du template de hook...")

        hook_template = '''/// <reference path="../types/pocketbase.d.ts" />

onRecordAfterCreateRequest((e) => {
  console.log("Enregistrement créé:", e.record.getId());
  console.log("Collection:", e.record.collection.name);
}, "users");

onRecordAfterUpdateRequest((e) => {
  console.log("Enregistrement mis à jour:", e.record.getId());
}, "users");

// Exemple de hook personnalisé
routerAdd("GET", "/api/hello", (c) => {
  return c.json(200, { "message": "Hello from PocketBase!" });
});
'''

        hook_file = self.project_dir / 'pb_hooks_ts' / 'src' / 'entries' / 'main.pb.ts'
        with open(hook_file, 'w') as f:
            f.write(hook_template)
        print(f"  ✅ Template créé: src/entries/main.pb.ts")

        # Créer types/pocketbase.d.ts (stub)
        types_stub = '''// PocketBase Type Definitions
// Ces types seront générer par PocketBase à partir de pb_data/types.d.ts

declare global {
  function onBeforeServe(callback: () => void): void;
  function onAfterServe(callback: () => void): void;

  function onRecordAfterCreateRequest(
    callback: (e: any) => void,
    collection?: string
  ): void;

  function onRecordAfterUpdateRequest(
    callback: (e: any) => void,
    collection?: string
  ): void;

  function routerAdd(
    method: string,
    path: string,
    callback: (c: any) => any
  ): void;

  function $http: any;
  function $app: any;
}

export {};
'''

        types_file = self.project_dir / 'pb_hooks_ts' / 'src' / 'types' / 'pocketbase.d.ts'
        with open(types_file, 'w') as f:
            f.write(types_stub)
        print(f"  ✅ Types stub créé: src/types/pocketbase.d.ts")

        print("✅ Template de hook créé")

    def create_config_file(self):
        """Crée un fichier de configuration pour le projet"""
        config = {
            "port": self.pb_port,
            "version": self.pb_version
        }

        config_file = self.project_dir / 'pb_config.json'
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def create_run_script(self):
        """Crée un script run.sh pour lancer PocketBase"""
        print("\n🏃 Création du script run.sh...")

        run_script = rf"""#!/bin/bash

# Script pour lancer PocketBase avec la configuration du projet
# Usage: ./run.sh [--port PORT]

set -e

# Couleurs pour l'output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

# Port par défaut de la configuration
CONFIG_PORT={self.pb_port}

# Gérer les arguments du script
PORT=$CONFIG_PORT
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo -e "${{RED}}❌ Option inconnue: $1${{NC}}"
            echo "Usage: $0 [--port PORT]"
            exit 1
            ;;
    esac
done

# Vérifier que le binaire pocketbase existe
if [ ! -f "./pocketbase" ]; then
    echo -e "${{RED}}❌ Erreur: Le binaire pocketbase n'a pas été trouvé${{NC}}"
    echo "   Assurez-vous que vous êtes dans le dossier du projet"
    exit 1
fi

# Vérifier que les répertoires existent
for dir in pb_data pb_hooks pb_migration pb_public; do
    if [ ! -d "./$dir" ]; then
        echo -e "${{YELLOW}}⚠️  Création du répertoire $dir...${{NC}}"
        mkdir -p "$dir"
    fi
done

echo -e "${{GREEN}}🚀 Lancement de PocketBase${{NC}}"
echo "   📁 Répertoire de données: pb_data"
echo "   🪝 Répertoire des hooks: pb_hooks"
echo "   📦 Répertoire des migrations: pb_migration"
echo "   🌐 Répertoire public: pb_public"
echo "   🔌 Port: $PORT"
echo ""
echo -e "${{YELLOW}}L'application sera disponible à: http://localhost:$PORT${{NC}}"
echo -e "${{YELLOW}}Appuyez sur Ctrl+C pour arrêter${{NC}}"
echo ""

# Lancer PocketBase avec les paramètres
./pocketbase serve \\
    --dir=pb_data \\
    --hooksDir=pb_hooks \\
    --migrationsDir=pb_migration \\
    --publicDir=pb_public \\
    --http=127.0.0.1:$PORT
"""

        run_file = self.project_dir / 'run.sh'
        with open(run_file, 'w') as f:
            f.write(run_script)

        # Rendre le fichier exécutable
        os.chmod(run_file, 0o755)
        print(f"  ✅ Script run.sh créé et rendu exécutable")

    def create_gitignore(self):
        """Crée un fichier .gitignore pour le projet"""
        print("\n📄 Création du fichier .gitignore...")

        gitignore_content = """# Dependencies
node_modules/
package-lock.json
yarn.lock
pnpm-lock.yaml

# PocketBase data
pb_data/
!pb_data/.gitkeep

# Environment variables
.env
.env.local
.env.*.local

# IDE and editor
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
.sublime-project
.sublime-workspace

# OS
Thumbs.db
.DS_Store

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build output
dist/
build/
out/

# Compiled JavaScript from TypeScript
pb_hooks/*.js
pb_hooks/*.js.map

# Temporary files
*.tmp
.cache
"""

        gitignore_file = self.project_dir / '.gitignore'
        with open(gitignore_file, 'w') as f:
            f.write(gitignore_content)
        print(f"  ✅ .gitignore créé")

    def create_init_types_script(self):
        """Crée un script init-types.sh pour initialiser les types TypeScript"""
        print("\n📝 Création du script init-types.sh...")

        init_script = r"""#!/bin/bash

# Script pour initialiser les types TypeScript depuis PocketBase
# Ce script lance PocketBase, génère les types, puis les copie dans pb_hooks_ts
# Usage: ./init-types.sh

set -e

# Couleurs pour l'output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

echo -e "${BLUE}📝 Initialisation des types TypeScript${NC}"
echo ""

# Vérifier que le binaire pocketbase existe
if [ ! -f "./pocketbase" ]; then
    echo -e "${RED}❌ Erreur: Le binaire pocketbase n'a pas été trouvé${NC}"
    exit 1
fi

# Vérifier que pb_hooks_ts/src/types existe
if [ ! -d "./pb_hooks_ts/src/types" ]; then
    echo -e "${RED}❌ Erreur: Le dossier pb_hooks_ts/src/types n'existe pas${NC}"
    exit 1
fi

echo -e "${YELLOW}⏳ Lancement de PocketBase pour générer les types...${NC}"
echo "   (Attendre ~3 secondes)"

# Lancer PocketBase en arrière-plan
./pocketbase serve \\
    --dir=pb_data \\
    --hooksDir=pb_hooks \\
    --migrationsDir=pb_migration \\
    --publicDir=pb_public > /dev/null 2>&1 &

PB_PID=\$!

# Attendre que PocketBase démarre et génère les types
sleep 3

# Arrêter PocketBase
kill \$PB_PID 2>/dev/null || true
wait \$PB_PID 2>/dev/null || true

# Vérifier que le fichier types.d.ts a été généré
if [ ! -f "./pb_data/types.d.ts" ]; then
    echo -e "${RED}❌ Erreur: Le fichier pb_data/types.d.ts n'a pas été généré${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Types générés${NC}"
echo ""

# Copier les types dans pb_hooks_ts/src/types/
echo -e "${YELLOW}📋 Copie des types vers pb_hooks_ts/src/types/pocketbase.d.ts...${NC}"
cp ./pb_data/types.d.ts ./pb_hooks_ts/src/types/pocketbase.d.ts

echo -e "${GREEN}✅ Types copiés avec succès!${NC}"
echo ""
echo -e "${BLUE}Prochaines étapes:${NC}"
echo "  1. Modifiez vos hooks dans pb_hooks_ts/src/entries/"
echo "  2. Exécutez: cd pb_hooks_ts && npm run build"
echo "  3. Relancez PocketBase: ./run.sh"
echo ""
"""

        init_file = self.project_dir / 'init-types.sh'
        with open(init_file, 'w') as f:
            f.write(init_script)

        # Rendre le fichier exécutable
        os.chmod(init_file, 0o755)
        print(f"  ✅ Script init-types.sh créé et rendu exécutable")

    def create_readme(self):
        """Crée un README avec les instructions"""
        print("\n📄 Création du README...")

        readme = f"""# Projet PocketBase - {self.pb_version}

## Structure du projet

- **pb_hooks/** - Hooks compilés en JavaScript (généré automatiquement)
- **pb_hooks_ts/** - Projet TypeScript source
  - src/entries/ - Fichiers de hooks TypeScript (compilés vers pb_hooks/)
  - src/types/ - Définitions de types TypeScript
  - src/lib/ - Code utilitaire/librairie partagé
  - package.json - Dépendances et scripts
  - tsconfig.json - Configuration TypeScript
  - tsup.config.ts - Configuration du builder
- **pb_migration/** - Migrations de base de données
- **pb_public/** - Fichiers publics statiques
- **pb_data/** - Données de PocketBase
- **pocketbase** - Binaire PocketBase (pour macOS/Linux)

## Installation

1. **Initialiser les types TypeScript** (important - première fois uniquement):
   ```bash
   ./init-types.sh
   ```
   Ce script lance PocketBase une première fois pour générer les types, puis les copie dans `pb_hooks_ts/src/types/pocketbase.d.ts`

2. Installer les dépendances du projet TypeScript:
   ```bash
   cd pb_hooks_ts
   npm install
   ```

3. Compiler les hooks TypeScript:
   ```bash
   npm run build
   ```

4. Démarrer le mode watch (recompile automatiquement):
   ```bash
   npm run dev
   ```

## Lancer PocketBase

### Option 1: Utiliser le script automatique (recommandé)

```bash
./run.sh
```

Ce script va automatiquement:
- Vérifier que le binaire PocketBase existe
- Créer les dossiers s'ils n'existent pas
- Lancer PocketBase avec tous les paramètres configurés
- Utiliser le port configuré lors du setup (`{self.pb_port}`)

**Modifier le port à l'exécution:**

```bash
./run.sh --port 3000
```

Cela lancera PocketBase sur le port `3000` au lieu du port par défaut.

### Option 2: Commande manuelle

```bash
./pocketbase serve \\
    --dir=pb_data \\
    --hooksDir=pb_hooks \\
    --migrationsDir=pb_migration \\
    --publicDir=pb_public \\
    --http=127.0.0.1:{self.pb_port}
```

Les hooks seront chargés automatiquement depuis `pb_hooks/`.

L'application sera disponible à: **http://localhost:{self.pb_port}**

## Configuration

Lors du setup, vous avez configuré:
- **Port:** `{self.pb_port}`
- **Version:** `{self.pb_version}`

Ces paramètres sont sauvegardés dans `pb_config.json`

Pour modifier le port au lancement, utilisez `./run.sh --port PORT`

## Développement

- **Ajouter un nouveau hook:**
  - Créer un fichier dans `pb_hooks_ts/src/entries/`
  - Implémenter les hooks PocketBase (onRecordAfterCreateRequest, routerAdd, etc.)
  - Exécuter `npm run build` pour compiler
  - Les fichiers `.js` seront générés dans `pb_hooks/`

- **Mode watch:**
  - Exécutez `npm run dev` pour activer la recompilation automatique
  - Les modifications sont compilées automatiquement

- **Importer du code partagé:**
  - Placez le code réutilisable dans `src/lib/`
  - Importez-le dans vos hooks: import {{ foo }} from '../lib/utils.js';

## Cache des binaires

Le script `pb_setup.py` sauvegarde automatiquement les binaires PocketBase téléchargés dans:
```
~/.pb_cache/
```

Lors des prochains setups, les binaires seront utilisés depuis le cache au lieu d'être retéléchargés.

**Pour nettoyer le cache:**
```bash
rm -rf ~/.pb_cache/
```

## Ressources

- [PocketBase Docs](https://pocketbase.io/docs/)
- [JS Event Hooks](https://pocketbase.io/docs/js-overview/)
- [TypeScript](https://www.typescriptlang.org/)
"""

        with open(self.project_dir / 'README.md', 'w') as f:
            f.write(readme)
        print("✅ README.md créé")

    def run_setup(self):
        """Exécute l'installation complète"""
        print("🚀 Démarrage de la configuration PocketBase\n")

        # Sélectionner le dossier du projet
        self.select_project_dir()

        # Sélectionner le port
        self.select_port()

        # Sélectionner la version
        self.select_version()

        # Télécharger PocketBase
        if not self.download_pocketbase():
            print("❌ Impossible de télécharger PocketBase. Arrêt.")
            return

        # Créer la structure
        self.create_folder_structure()

        # Initialiser TypeScript
        self.initialize_typescript_project()

        # Créer le template de hook
        self.create_hook_template()

        # Créer le fichier .gitignore
        self.create_gitignore()

        # Créer le script run.sh
        self.create_run_script()

        # Créer le fichier de configuration
        self.create_config_file()

        # Créer le script init-types.sh
        self.create_init_types_script()

        # Créer README
        self.create_readme()

        print("\n" + "="*50)
        print("✅ Configuration terminée avec succès!")
        print("="*50)
        print("\n📝 Prochaines étapes:")
        print(f"  1. cd {self.project_dir}")
        print("  2. ./init-types.sh  # Initialiser les types TypeScript (1ère fois)")
        print("  3. cd pb_hooks_ts && npm install")
        print("  4. npm run build")
        print("  5. cd ..")
        print("  6. ./run.sh         # Lancer PocketBase automatiquement")
        print("\n📖 Pour plus d'informations, consultez le README.md")
        print("\n")


def print_usage():
    """Affiche l'aide d'utilisation"""
    print("""
🚀 PocketBase Project Setup Tool

Usage:
  pb_setup [PROJECT_DIR] [OPTIONS]

Arguments:
  PROJECT_DIR           Chemin du dossier du projet (obligatoire ou demandé)

Options:
  --version VERSION     Version de PocketBase à télécharger (ex: v0.30.3)
  --port PORT          Port pour PocketBase (défaut: 8090, range: 1024-65535)
  -h, --help           Affiche cette aide

Examples:
  pb_setup
                        Mode interactif - demande tous les paramètres

  pb_setup ~/my_project
                        Crée un projet dans ~/my_project (port & version interactif)

  pb_setup ~/my_project --port 3000
                        Crée un projet avec port personnalisé

  pb_setup ~/my_project --version v0.30.3
                        Crée un projet avec version spécifique

  pb_setup ~/my_project --version v0.30.3 --port 3000
                        Crée un projet avec version et port spécifiques
""")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        prog='pb_setup',
        description='Automatise la création d\'un projet PocketBase avec hooks TypeScript',
        add_help=False
    )

    parser.add_argument('project_dir', nargs='?', help='Chemin du dossier du projet')
    parser.add_argument('--version', dest='version', help='Version de PocketBase (ex: v0.30.3)')
    parser.add_argument('--port', dest='port', type=int, help='Port pour PocketBase (1024-65535)')
    parser.add_argument('-h', '--help', action='store_true', help='Affiche cette aide')

    args = parser.parse_args()

    if args.help:
        print_usage()
        sys.exit(0)

    # Valider le port si fourni
    if args.port is not None:
        if not (1024 <= args.port <= 65535):
            print(f"❌ Le port doit être entre 1024 et 65535, reçu: {args.port}")
            sys.exit(1)

    # Créer l'instance avec les paramètres
    setup = PocketBaseSetup(
        project_dir=args.project_dir,
        pb_version=args.version,
        pb_port=args.port
    )

    # Marquer si le port vient des arguments
    if args.port is not None:
        setup._port_from_args = True

    setup.run_setup()


if __name__ == "__main__":
    main()
