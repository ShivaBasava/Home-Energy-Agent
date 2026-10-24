"""RAG store (Chroma) and knowledge graph (rdflib) helpers."""
from pathlib import Path
import chromadb
from rdflib import Graph
from embeddings import Embedder

ROOT = Path(__file__).parent
_collection = None
_graph = None

def _chunks(path: Path):
    """Split a markdown file into one chunk per non-heading line (keeps facts atomic)."""
    for i, line in enumerate(path.read_text().splitlines()):
        if line.strip() and not line.startswith("#"):
            yield f"{path.stem}-{i}", line.strip(), {"source": path.name}

def collection():
    global _collection
    if _collection is None:
        client = chromadb.EphemeralClient()
        _collection = client.get_or_create_collection("energy_notes", embedding_function=Embedder())
        ids, docs, metas = [], [], []
        for p in sorted((ROOT / "data" / "knowledge").glob("*.md")):
            for cid, text, meta in _chunks(p):
                ids.append(cid); docs.append(text); metas.append(meta)
        _collection.add(ids=ids, documents=docs, metadatas=metas)
    return _collection

def graph() -> Graph:
    global _graph
    if _graph is None:
        _graph = Graph()
        _graph.parse(ROOT / "data" / "kg.ttl", format="turtle")
    return _graph

def search(query: str, k: int = 3):
    res = collection().query(query_texts=[query], n_results=k)
    return [{"text": d, "source": m["source"]} for d, m in zip(res["documents"][0], res["metadatas"][0])]

def sparql_select(query: str):
    if not query.lstrip().upper().startswith(("SELECT", "PREFIX")):
        raise ValueError("Only read-only SELECT queries are allowed")
    if any(w in query.upper() for w in ("INSERT", "DELETE", "DROP", "CLEAR", "LOAD")):
        raise ValueError("Update operations are not allowed")
    rows = graph().query(query)
    return [{str(k): str(v).split("#")[-1] for k, v in r.asdict().items()} for r in rows]

def _norm(x: str) -> str:
    return "".join(ch for ch in x.lower() if ch.isalnum())

def resolve(name: str):
    """Map a loosely written name ('self-consumption', 'battery storage') to a graph entity id."""
    rows = sparql_select("""PREFIX ex: <http://example.org/energy#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?e ?l WHERE { ?e rdfs:label ?l }""")
    for r in rows:
        if _norm(name) in (_norm(r["e"]), _norm(r["l"])):
            return r["e"]
    return None

def entities():
    return sorted(r["e"] for r in sparql_select("""PREFIX ex: <http://example.org/energy#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> SELECT ?e WHERE { ?e rdfs:label ?l }"""))

def influencers(metric: str):
    ent = resolve(metric)
    if ent is None:
        return {"error": f"unknown metric '{metric}'", "valid_entities": entities()}
    rows = sparql_select(f"""PREFIX ex: <http://example.org/energy#>
        SELECT ?component WHERE {{ ?component ex:influences ex:{ent} }}""")
    return {"metric": ent, "components_that_influence_it": [r["component"] for r in rows]}

def neighbors(entity: str):
    resolved = resolve(entity)
    if resolved is None:
        return {"error": f"unknown entity '{entity}'", "valid_entities": entities()}
    entity = resolved
    q = f"""PREFIX ex: <http://example.org/energy#>
    SELECT ?p ?o WHERE {{ ex:{entity} ?p ?o . FILTER(?p != <http://www.w3.org/1999/02/22-rdf-syntax-ns#type>) }}"""
    out = sparql_select(q)
    inbound = sparql_select(f"""PREFIX ex: <http://example.org/energy#>
    SELECT ?s ?p WHERE {{ ?s ?p ex:{entity} . }}""")
    return {"outgoing": out, "incoming": inbound}
