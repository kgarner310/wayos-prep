"""Saved artifact persistence service."""

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.models import SavedArtifact

logger = logging.getLogger(__name__)


def save_artifact(db: Session, data: dict) -> SavedArtifact:
    """Save a generated artifact."""
    artifact = SavedArtifact(
        account_id=data.get("account_id"),
        artifact_type=data["artifact_type"],
        artifact_subtype=data.get("artifact_subtype"),
        title=data.get("title", ""),
        content_json=data["content_json"],
        rendered_text=data.get("rendered_text"),
        status=data.get("status", "ready"),
        confidence=data.get("confidence"),
        model_name=data.get("model_name"),
        created_by_user_id=data.get("created_by_user_id"),
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    logger.info(
        "Artifact saved: id=%s type=%s account=%s",
        artifact.id, artifact.artifact_type, artifact.account_id,
    )
    return artifact


def get_artifact(db: Session, artifact_id: UUID) -> SavedArtifact | None:
    """Get an artifact by ID."""
    return db.query(SavedArtifact).filter(SavedArtifact.id == artifact_id).first()


def list_artifacts_for_account(
    db: Session, account_id: UUID, limit: int = 50
) -> list[SavedArtifact]:
    """List artifacts linked to an account."""
    return (
        db.query(SavedArtifact)
        .filter(SavedArtifact.account_id == account_id)
        .order_by(SavedArtifact.created_at.desc())
        .limit(limit)
        .all()
    )
