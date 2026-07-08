// Worker relais TDF Live.
//
// Le Mac POUSSE le snapshot :  PUT /race/current  (Authorization: Bearer <TOKEN>)
// L'app / le widget le LISENT :  GET /race/current  (public, sans cache)
//
// Le snapshot est stocké dans un namespace KV (binding "TDF"). Le token est un
// secret Worker (PUBLISH_TOKEN). Voir README.md pour le déploiement.

const KEY = "current";

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",           // toujours frais : le widget doit voir la dernière minute
  "access-control-allow-origin": "*",
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== "/race/current") {
      return new Response("not found", { status: 404 });
    }

    // --- Écriture (depuis le Mac) ------------------------------------------
    if (request.method === "PUT" || request.method === "POST") {
      const token = (request.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
      if (!env.PUBLISH_TOKEN || token !== env.PUBLISH_TOKEN) {
        return new Response("unauthorized", { status: 401 });
      }
      const body = await request.text();
      await env.TDF.put(KEY, body);
      return new Response("ok", { status: 200 });
    }

    // --- Lecture (app / widget) --------------------------------------------
    if (request.method === "GET") {
      const body = await env.TDF.get(KEY);
      if (body === null) {
        // Rien encore publié : renvoie un état "hors course" plutôt qu'une erreur.
        return new Response(
          JSON.stringify({ live: false, stage: null, kmToFinish: null, groups: [], updatedAt: null }),
          { status: 200, headers: JSON_HEADERS },
        );
      }
      return new Response(body, { status: 200, headers: JSON_HEADERS });
    }

    return new Response("method not allowed", { status: 405 });
  },
};
