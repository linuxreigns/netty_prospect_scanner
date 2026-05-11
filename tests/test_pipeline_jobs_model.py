import json
from uuid import uuid4

from app.database import SessionLocal
from app.models import PipelineJob


def test_pipeline_job_persistence_roundtrip():
    db = SessionLocal()
    try:
        job_id = str(uuid4())
        job = PipelineJob(
            job_id=job_id,
            status="queued",
            payload_json=json.dumps({"rubro": "restaurantes", "limit": 1}),
            attempts=0,
            max_attempts=3,
            phase="queued",
        )
        db.add(job)
        db.commit()

        found = db.query(PipelineJob).filter(PipelineJob.job_id == job_id).first()
        assert found is not None
        assert found.status == "queued"
        assert json.loads(found.payload_json)["rubro"] == "restaurantes"
    finally:
        db.close()
