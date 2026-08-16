import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from forecastos.data.csv_loader import load_csv_data
from forecastos.data.validation import ValidationError
from forecastos.storage.database import get_db
from forecastos.storage.models import DatasetModel
from forecastos.blockchain.hash import generate_dataset_hash
from forecastos.api.schemas import DatasetListResponse, DatasetResponse

router = APIRouter(prefix="/api/v1/datasets", tags=["Datasets"])


@router.post("", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload and validate CSV/JSON time-series dataset."""
    filename = file.filename or "dataset.csv"
    if not (filename.endswith(".csv") or filename.endswith(".json")):
        raise HTTPException(status_code=400, detail="File must be a CSV or JSON format.")

    content = await file.read()
    try:
        validated = load_csv_data(file_content=content, filename=filename)
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e))

    dataset_id = f"ds_{uuid.uuid4().hex[:12]}"
    dataset_hash = generate_dataset_hash(validated["values"], validated["dates"])

    db_dataset = DatasetModel(
        id=dataset_id,
        name=filename.rsplit(".", 1)[0].replace("_", " ").title(),
        filename=filename,
        row_count=validated["row_count"],
        frequency=validated["frequency"],
        start_date=validated["start_date"],
        end_date=validated["end_date"],
        dataset_hash=dataset_hash,
    )
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)

    return DatasetResponse(
        id=db_dataset.id,
        name=db_dataset.name,
        filename=db_dataset.filename,
        row_count=db_dataset.row_count,
        frequency=db_dataset.frequency,
        start_date=db_dataset.start_date,
        end_date=db_dataset.end_date,
        dataset_hash=db_dataset.dataset_hash,
        created_at=db_dataset.created_at.isoformat(),
    )


@router.get("", response_model=DatasetListResponse)
def list_datasets(db: Session = Depends(get_db)):
    """List all uploaded time-series datasets."""
    datasets = db.query(DatasetModel).order_by(DatasetModel.created_at.desc()).all()
    resp_list = [
        DatasetResponse(
            id=d.id,
            name=d.name,
            filename=d.filename,
            row_count=d.row_count,
            frequency=d.frequency,
            start_date=d.start_date,
            end_date=d.end_date,
            dataset_hash=d.dataset_hash,
            created_at=d.created_at.isoformat(),
        )
        for d in datasets
    ]
    return DatasetListResponse(datasets=resp_list, total=len(resp_list))


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific dataset."""
    db_dataset = db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
    if not db_dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    return DatasetResponse(
        id=db_dataset.id,
        name=db_dataset.name,
        filename=db_dataset.filename,
        row_count=db_dataset.row_count,
        frequency=db_dataset.frequency,
        start_date=db_dataset.start_date,
        end_date=db_dataset.end_date,
        dataset_hash=db_dataset.dataset_hash,
        created_at=db_dataset.created_at.isoformat(),
    )
