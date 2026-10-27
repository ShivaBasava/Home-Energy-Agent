"""Following a modular approach for testing. Fast, deterministic tests for the tool logic. They need no Ollama and no language model."""
import os, sys
from pathlib import Path

os.environ.setdefault("EMBED_BACKEND", "hash")  # for offline embeddings for the test run
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import knowledge
import mcp_server


class TestGraphLookup:
    def test_resolve_accepts_loose_names(self):
        assert knowledge.resolve("self-consumption") == "SelfConsumption"
        assert knowledge.resolve("battery storage") == "BatteryStorage"
        assert knowledge.resolve("no such thing") is None

    def test_unknown_entity_lists_valid_names(self):
        result = knowledge.neighbors("no such thing")
        assert "error" in result and "BatteryStorage" in result["valid_entities"]

    def test_influencers_follow_the_graph(self):
        assert knowledge.influencers("SelfConsumption")["components_that_influence_it"] == ["BatteryStorage"]
        assert "HeatPump" in knowledge.influencers("Demand")["components_that_influence_it"]


class TestSparqlGuard:
    @pytest.mark.parametrize("query", [
        "INSERT DATA { <a> <b> <c> }",
        "PREFIX ex: <http://example.org/energy#> SELECT ?s WHERE { ?s ?p ?o } ; DROP ALL",
    ])
    def test_rejects_updates(self, query):
        with pytest.raises(ValueError):
            knowledge.sparql_select(query)


class TestSearch:
    def test_returns_requested_number_of_chunks(self):
        assert len(knowledge.search("battery", k=2)) == 2


class TestYieldEstimate:
    def test_south_roof_is_plausible(self):
        assert 7000 < mcp_server.estimate_pv_yield_kwh(kwp=8)["annual_kwh"] < 8000

    def test_east_roof_yields_less_than_south(self):
        south = mcp_server.estimate_pv_yield_kwh(kwp=8)
        east = mcp_server.estimate_pv_yield_kwh(kwp=8, azimuth_deg=90)
        assert east["annual_kwh"] < south["annual_kwh"]
