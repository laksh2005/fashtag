# AI Engineer Hiring Assignment - Fashion Attribute Classification App (FashTag)

This project implements the required end-to-end application:

- Scrapes clothing product images + metadata from Myntra
- Prepares labels:
  - Gender: `male` / `female`
  - Sleeve type: `full_sleeve` / `half_sleeve`
- Trains/fine-tunes an image classifier (transfer learning)
- Supports prediction for a single item and a batch of items
- Provides a simple UI to view products, trigger predictions, and view prediction history
- Stores prediction tracking records in a SQLite database (no images in DB)

## Setup

```powershell
cd E:\fashtag
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Step 1: Scrape Data (Myntra)

Scrape images + build `data\metadata\metadata.csv`:

```powershell
python -m scraper.scraper --target-per-class 250
```

Verify dataset counts:

```powershell
python -m scraper.dataset_summary
```

## Step 2: Train Model (Required)

Train the multi-task model (gender + sleeve):

```powershell
python -m training.train --epochs 8 --batch-size 16
```

Artifacts:

- `models\checkpoints\best_multitask_resnet18.pt`
- `models\checkpoints\training_history.csv`
- `models\checkpoints\final_metrics.json`

## Step 3: Run Predictions (API + UI)

Start the backend:

```powershell
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open the UI:

- Next.js (dev):

```powershell
cd E:\fashtag\ui
npm install
npm run dev
```

- Open `http://127.0.0.1:3000/`

API endpoints:

- `GET /products`
- `POST /predict-single`
- `POST /predict-batch`
- `GET /history`
- `GET /health`

## Database Requirement

SQLite database file:

- `database\predictions.db`

Prediction tracking fields stored (minimum):

- Image URL/reference
- Run type: `single` / `batch`
- Run ID / Batch ID
- Predicted gender
- Predicted sleeve type
- Confidence score(s)
- Model name/version
- Timestamp
- Status / error message

## Deliverables

Demo video:
- Show scrape output (dataset summary), a training run saving a checkpoint, UI single prediction, UI batch prediction, and prediction history updating.

## Short Note

Approach:
- Scrape Myntra product images into 4 buckets and write metadata to CSV.
- Train one transfer-learning model with a shared CNN backbone and two heads (gender + sleeve).
- Serve inference via FastAPI and log each prediction to SQLite.
- UI calls the API to run single/batch predictions and display history.

Model choice:
- Pretrained `ResNet18` backbone for fast, reliable fine-tuning on a small dataset.
- Multi-task heads reduce duplication and simplify deployment.

Limitations:
- Scraped labels are noisy and the dataset can be imbalanced.
- Scraping can break if Myntra DOM changes or rate-limits requests.
- Metrics are from a small validation split; may not generalize broadly.

Improvements with more time:
- Balance/expand dataset and add manual QA for labels.
- Add richer evaluation outputs (confusion matrices, misclassification review).
- Better model versioning/monitoring and UI to compare model runs.
