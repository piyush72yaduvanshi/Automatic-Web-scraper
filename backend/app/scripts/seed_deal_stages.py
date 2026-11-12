#!/usr/bin/env python3
"""Seed default deal stages for the Default Sales Pipeline."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.core.database import SessionLocal
from app.models.crm import Pipeline, PipelineStage
import uuid


def seed_deal_stages():
    """Seed default pipeline with 7 stages."""
    db = SessionLocal()
    
    try:
        # Find or create Default Sales Pipeline
        pipeline = db.query(Pipeline).filter(Pipeline.is_default == True).first()
        
        if not pipeline:
            print("Creating Default Sales Pipeline...")
            pipeline = Pipeline(
                id=uuid.uuid4(),
                name="Default Sales Pipeline",
                is_default=True,
            )
            db.add(pipeline)
            db.commit()
            db.refresh(pipeline)
            print(f"✓ Created pipeline: {pipeline.name}")
        else:
            print(f"Found existing pipeline: {pipeline.name}")
        
        # Define the 7 stages
        stages_data = [
            {"name": "Lead", "stage_order": 1, "probability": 0.10, "is_closed_won": False, "is_closed_lost": False},
            {"name": "Qualified", "stage_order": 2, "probability": 0.20, "is_closed_won": False, "is_closed_lost": False},
            {"name": "Demo Scheduled", "stage_order": 3, "probability": 0.40, "is_closed_won": False, "is_closed_lost": False},
            {"name": "Proposal Sent", "stage_order": 4, "probability": 0.60, "is_closed_won": False, "is_closed_lost": False},
            {"name": "Negotiation", "stage_order": 5, "probability": 0.80, "is_closed_won": False, "is_closed_lost": False},
            {"name": "Closed Won", "stage_order": 6, "probability": 1.0, "is_closed_won": True, "is_closed_lost": False},
            {"name": "Closed Lost", "stage_order": 7, "probability": 0.0, "is_closed_won": False, "is_closed_lost": True},
        ]
        
        # Check existing stages
        existing_stages = db.query(PipelineStage).filter(PipelineStage.pipeline_id == pipeline.id).all()
        existing_stage_names = {s.name for s in existing_stages}
        
        print(f"\nExisting stages: {len(existing_stages)}")
        
        # Create or update stages
        for stage_data in stages_data:
            if stage_data["name"] in existing_stage_names:
                # Update existing stage
                stage = db.query(PipelineStage).filter(
                    PipelineStage.pipeline_id == pipeline.id,
                    PipelineStage.name == stage_data["name"]
                ).first()
                
                stage.stage_order = stage_data["stage_order"]
                stage.probability = stage_data["probability"]
                stage.is_closed_won = stage_data["is_closed_won"]
                stage.is_closed_lost = stage_data["is_closed_lost"]
                
                print(f"✓ Updated stage: {stage_data['name']} (order={stage_data['stage_order']}, prob={stage_data['probability']})")
            else:
                # Create new stage
                stage = PipelineStage(
                    id=uuid.uuid4(),
                    pipeline_id=pipeline.id,
                    name=stage_data["name"],
                    stage_order=stage_data["stage_order"],
                    probability=stage_data["probability"],
                    is_closed_won=stage_data["is_closed_won"],
                    is_closed_lost=stage_data["is_closed_lost"],
                )
                db.add(stage)
                print(f"✓ Created stage: {stage_data['name']} (order={stage_data['stage_order']}, prob={stage_data['probability']})")
        
        db.commit()
        print(f"\n✅ Successfully seeded {len(stages_data)} deal stages")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding deal stages: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_deal_stages()
