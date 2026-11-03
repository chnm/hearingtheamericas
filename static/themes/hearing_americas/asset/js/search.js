/* Client-side search for the hearingtheamericas.org archive.
 *
 * Omeka S served search from /s/the-americas/index/search, a database query.
 * A static archive has no database, so the search box the theme put in the
 * header of all 963 pages was posting to an endpoint that no longer exists --
 * and the crawl had rewritten its action to the absolute origin URL, so once
 * the DNS moves it would not even have failed locally.
 *
 * This drives Pagefind's prebuilt index instead, from /pagefind/, which is
 * committed to the repository so the deploy stays a plain file copy.
 *
 * Pagefind's Default UI is not used: it renders its own search box, which
 * would be a second one on a page whose header already carries the site-wide
 * form. On this page that header form IS the search form -- it keeps its
 * place, its styling and its shape, and this reads the query straight out of
 * the URL.
 *
 * The query parameter is `fulltext_search`, the name Omeka S itself used, so
 * links and bookmarks of the old shape still land on a real result set. `q`
 * and `query` are accepted too.
 */

const form = document.getElementById("search-form");
const input = form.querySelector('input[name="fulltext_search"]');
const status = document.getElementById("search-status");
const results = document.getElementById("search-results");

const MAX = 100;

let pagefind = null;

async function library() {
  if (!pagefind) {
    pagefind = await import("/pagefind/pagefind.js");
    await pagefind.init();
  }
  return pagefind;
}

function queryFromUrl() {
  const p = new URLSearchParams(window.location.search);
  return (p.get("fulltext_search") || p.get("q") || p.get("query") || "").trim();
}

function titleOf(hit) {
  const t = (hit.meta && hit.meta.title) || hit.url;
  // Every page's <title> ends in " · Hearing the Americas". In a list of
  // results from one archive that is noise repeated on every row.
  return t.replace(/\s*·\s*Hearing the Americas\s*$/, "");
}

function render(query, hits) {
  results.replaceChildren();
  if (!hits.length) {
    status.textContent = `No results for “${query}”.`;
    return;
  }
  status.textContent =
    hits.length === 1
      ? `1 result for “${query}”.`
      : `${hits.length} results for “${query}”.`;
  const ol = document.createElement("ol");
  ol.className = "search-result-list";
  for (const hit of hits) {
    const li = document.createElement("li");
    const h2 = document.createElement("h2");
    h2.className = "search-result-title";
    const a = document.createElement("a");
    a.href = hit.url;
    a.textContent = titleOf(hit);
    h2.append(a);
    const p = document.createElement("p");
    p.className = "search-result-excerpt";
    p.innerHTML = hit.excerpt; // Pagefind's own <mark>-wrapped, escaped text
    li.append(h2, p);
    ol.append(li);
  }
  results.append(ol);
}

async function run(query) {
  if (!query) {
    results.replaceChildren();
    status.textContent = "Enter a word or phrase to search the archive.";
    return;
  }
  status.textContent = `Searching for “${query}”…`;
  try {
    const pf = await library();
    const search = await pf.search(query);
    const hits = await Promise.all(
      search.results.slice(0, MAX).map((r) => r.data())
    );
    render(query, hits);
  } catch (e) {
    status.textContent = "The search index could not be loaded.";
    console.error(e);
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const query = input.value.trim();
  const url = new URL(window.location.href);
  url.search = query ? `?fulltext_search=${encodeURIComponent(query)}` : "";
  history.replaceState(null, "", url);
  run(query);
});

const initial = queryFromUrl();
input.value = initial;
run(initial);
