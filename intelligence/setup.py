from intelligence.factory import create_source
from intelligence.ingestion import (
    IntelligenceIngestionEngine,
)
from intelligence.registry import (
    IntelligenceSourceRegistry,
)


def build_ingestion_engine(
    registry: IntelligenceSourceRegistry,
) -> IntelligenceIngestionEngine:
    """Build an ingestion engine from the enabled source registry."""

    ingestion = IntelligenceIngestionEngine()

    for config in registry.enabled_sources():
        source = create_source(config)
        ingestion.add_source(source)

    return ingestion