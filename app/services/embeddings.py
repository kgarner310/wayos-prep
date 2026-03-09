"""Embedding generation service using OpenAI."""

import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import SourceChunk, ChunkEmbedding

logger = logging.getLogger(__name__)


def embed_chunks(db: Session, chunks: list[SourceChunk]) -> int:
    """Generate embeddings for chunks that don't already have them.

    Returns count of newly embedded chunks.
    """
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-your"):
        logger.warning("No OpenAI API key configured - skipping embedding generation")
        return 0

    import openai
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    # Filter out chunks that already have embeddings
    to_embed = []
    for chunk in chunks:
        existing = db.query(ChunkEmbedding).filter(
            ChunkEmbedding.chunk_id == chunk.id
        ).first()
        if not existing:
            to_embed.append(chunk)

    if not to_embed:
        logger.info("All chunks already have embeddings")
        return 0

    # Batch embed (OpenAI supports up to 2048 inputs per call)
    batch_size = 100
    embedded_count = 0

    for i in range(0, len(to_embed), batch_size):
        batch = to_embed[i:i + batch_size]
        texts = [c.text_content for c in batch]

        try:
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=texts,
                dimensions=settings.EMBEDDING_DIMENSIONS,
            )

            for j, emb_data in enumerate(response.data):
                chunk = batch[j]
                chunk_embedding = ChunkEmbedding(
                    chunk_id=chunk.id,
                    embedding=emb_data.embedding,
                    embedding_model=settings.EMBEDDING_MODEL,
                )
                db.add(chunk_embedding)
                embedded_count += 1

            db.commit()
            logger.info(f"Embedded batch {i // batch_size + 1}: {len(batch)} chunks")

        except Exception as e:
            logger.error(f"Embedding batch failed: {e}")
            db.rollback()
            raise

    return embedded_count


def get_query_embedding(text: str) -> list[float] | None:
    """Get embedding for a query string."""
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-your"):
        logger.warning("No OpenAI API key - cannot generate query embedding")
        return None

    import openai
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    response = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=[text],
        dimensions=settings.EMBEDDING_DIMENSIONS,
    )

    return response.data[0].embedding
