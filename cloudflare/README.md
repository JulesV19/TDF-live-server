# Worker relais TDF Live

Rend le snapshot accessible **hors du réseau local** : le Mac pousse `current.json`
vers ce Worker, l'app/le widget le lisent depuis n'importe où (4G, autre Wi-Fi…),
en HTTPS, sans VPN ni port ouvert.

```
Mac (server/)  --PUT /race/current-->  Worker + KV  <--GET /race/current--  iPhone
                 (Bearer TOKEN)                              (public)
```

## Déploiement (une fois)

```bash
npm i -g wrangler            # si pas déjà installé
cd cloudflare
wrangler login              # ouvre le navigateur, connecte ton compte Cloudflare

# 1) crée le namespace KV, copie l'"id" affiché dans wrangler.toml
wrangler kv namespace create TDF

# 2) choisis un token secret (long, aléatoire) pour autoriser le Mac à écrire
wrangler secret put PUBLISH_TOKEN     # colle le token quand il le demande

# 3) déploie
wrangler deploy
```

`wrangler deploy` affiche l'URL publique, du type :
`https://tdf-live.<ton-sous-domaine>.workers.dev`

## Ensuite

**Côté Mac** — donne au serveur l'URL + le même token (voir `../server/.env.example`) :

```bash
export TDF_PUBLISH_URL="https://tdf-live.<ton-sous-domaine>.workers.dev/race/current"
export TDF_PUBLISH_TOKEN="<le token choisi ci-dessus>"
./run.sh --mock        # (ou ./run.sh en course)
```

**Côté iOS** — mets la même URL de base dans les deux `ServerConfig` :
`TDF Live/TDF Live/RaceKit.swift` et `TDF Live/TDFWidget/ServerConfig.swift` :

```swift
static let baseURL = "https://tdf-live.<ton-sous-domaine>.workers.dev"
```

## Vérifier

```bash
# lecture publique (doit répondre du JSON)
curl https://tdf-live.<sous-domaine>.workers.dev/race/current

# écriture refusée sans token (doit répondre 401)
curl -X PUT https://tdf-live.<sous-domaine>.workers.dev/race/current -d '{}'
```
