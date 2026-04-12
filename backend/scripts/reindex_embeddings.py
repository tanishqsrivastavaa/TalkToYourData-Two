from __future__ import annotations

import argparse
import asyncio

from backend.app.db.session import SessionLocal
from backend.app.modules.maintenance.service import EmbeddingMaintenanceService


async def run(batch_size: int) -> None:
    async with SessionLocal() as session:
        service = EmbeddingMaintenanceService(session)
        stale_before = await service.count_stale_chunks()
        result = await service.reindex_stale_embeddings(batch_size=batch_size)
        stale_after = await service.count_stale_chunks()

    print(
        "Reindex complete:",
        f"stale_before={stale_before}",
        f"chunks_reindexed={result.chunks_reindexed}",
        f"documents_touched={result.documents_touched}",
        f"stale_after={stale_after}",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Reindex stale document chunk embeddings.")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of chunks to re-embed per batch.")
    args = parser.parse_args()
    asyncio.run(run(batch_size=args.batch_size))


if __name__ == "__main__":
    main()
