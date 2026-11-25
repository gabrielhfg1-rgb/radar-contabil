/* Service worker: deixa o painel abrir rápido e funcionar sem internet
   (mostra a última versão baixada). Ao mudar arquivos do painel, aumente a VERSAO. */
const VERSAO = "radar-v10";
const ARQUIVOS = [
  "./", "index.html", "estilo.css?v=10", "futurista.css?v=10", "app.js?v=10", "manifest.webmanifest",
  "icones/icone.svg", "icones/icone-192.png", "icones/icone-512.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSAO).then((c) => c.addAll(ARQUIVOS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((chaves) => Promise.all(chaves.filter((k) => k !== VERSAO).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;

  if (url.pathname.includes("/dados/")) {
    // Dados: tenta a internet primeiro; sem conexão, usa a cópia guardada.
    e.respondWith(
      fetch(e.request).then((resp) => {
        const copia = resp.clone();
        if (resp.ok) caches.open(VERSAO).then((c) => c.put(e.request, copia));
        return resp;
      }).catch(() => caches.match(e.request))
    );
    return;
  }
  // Painel: abre da cópia guardada e atualiza em segundo plano.
  e.respondWith(
    caches.match(e.request).then((guardado) => {
      const rede = fetch(e.request).then((resp) => {
        if (resp.ok) { const copia = resp.clone(); caches.open(VERSAO).then((c) => c.put(e.request, copia)); }
        return resp;
      }).catch(() => guardado);
      return guardado || rede;
    })
  );
});
