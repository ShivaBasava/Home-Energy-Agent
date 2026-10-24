"""MCP server exposing RAG, knowledge-graph and a PV yield estimator as tools."""
from mcp.server.fastmcp import FastMCP
import knowledge

mcp = FastMCP("home-energy-tools", log_level="WARNING")

@mcp.tool()
def search_knowledge(query: str, k: int = 3) -> list[dict]:
    """Semantic search over energy notes (photovoltaics, battery storage, heat pumps)."""
    return knowledge.search(query, k)

@mcp.tool()
def kg_neighbors(entity: str) -> dict:
    """Return incoming and outgoing relations of a knowledge-graph entity, e.g. PVWithBattery, BatteryStorage."""
    return knowledge.neighbors(entity)

@mcp.tool()
def kg_influencers(metric: str) -> dict:
    """List the components that influence a metric (e.g. SelfConsumption, AnnualYield, Cost, Demand)."""
    return knowledge.influencers(metric)

@mcp.tool()
def kg_sparql(query: str) -> list[dict]:
    """Run a read-only SPARQL SELECT over the energy knowledge graph (prefix ex: <http://example.org/energy#>)."""
    return knowledge.sparql_select(query)

@mcp.tool()
def estimate_pv_yield_kwh(kwp: float, tilt_deg: float = 35.0, azimuth_deg: float = 180.0,
                          irradiation_kwh_m2: float = 1100.0, performance_ratio: float = 0.85) -> dict:
    """Simplified annual PV yield estimate. azimuth: 180 = south, 90 = east, 270 = west."""
    tilt_factor = max(0.0, 1 - 0.00012 * (tilt_deg - 35) ** 2)
    az_dev = abs(azimuth_deg - 180)
    az_factor = max(0.0, 1 - 0.000018 * az_dev ** 2)
    annual = kwp * irradiation_kwh_m2 * performance_ratio * tilt_factor * az_factor
    return {"annual_kwh": round(annual), "specific_yield_kwh_per_kwp": round(annual / kwp),
            "orientation_factor": round(tilt_factor * az_factor, 3)}

if __name__ == "__main__":
    mcp.run()
