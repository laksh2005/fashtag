from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision.models import ResNet18_Weights
from torchvision.transforms import v2

from training.dataset import (
    FashionMultiTaskDataset,
    build_train_val_split,
    load_clean_metadata,
)
from training.model import MultiTaskResNet18


@dataclass
class EpochMetrics:
    epoch: int
    train_loss: float
    val_loss: float
    train_gender_acc: float
    train_sleeve_acc: float
    val_gender_acc: float
    val_sleeve_acc: float
    val_avg_acc: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train multitask ResNet18 for FashTag.")
    parser.add_argument("--metadata-csv", type=Path, default=Path("data/metadata/metadata.csv"))
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--val-size", type=float, default=0.2)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--freeze-backbone", action="store_true")
    parser.add_argument("--checkpoint-dir", type=Path, default=Path("models/checkpoints"))
    return parser.parse_args()


def set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def accuracy(logits: torch.Tensor, targets: torch.Tensor) -> float:
    preds = logits.argmax(dim=1)
    return (preds == targets).float().mean().item()


def run_epoch(
    model: nn.Module,
    loader: DataLoader,
    *,
    gender_criterion: nn.Module,
    sleeve_criterion: nn.Module,
    optimizer: torch.optim.Optimizer | None,
    device: torch.device,
) -> tuple[float, float, float]:
    is_train = optimizer is not None
    model.train(is_train)

    total_loss = 0.0
    total_gender_acc = 0.0
    total_sleeve_acc = 0.0
    batches = 0

    for images, target in loader:
        images = images.to(device)
        gender_target = target["gender"].to(device)
        sleeve_target = target["sleeve"].to(device)

        with torch.set_grad_enabled(is_train):
            output = model(images)
            gender_logits = output["gender_logits"]
            sleeve_logits = output["sleeve_logits"]

            gender_loss = gender_criterion(gender_logits, gender_target)
            sleeve_loss = sleeve_criterion(sleeve_logits, sleeve_target)
            loss = gender_loss + sleeve_loss

            if is_train:
                optimizer.zero_grad(set_to_none=True)
                loss.backward()
                optimizer.step()

        total_loss += loss.item()
        total_gender_acc += accuracy(gender_logits, gender_target)
        total_sleeve_acc += accuracy(sleeve_logits, sleeve_target)
        batches += 1

    if batches == 0:
        raise RuntimeError("Dataloader returned zero batches.")

    return (
        total_loss / batches,
        total_gender_acc / batches,
        total_sleeve_acc / batches,
    )


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    project_root = Path(__file__).resolve().parents[1]
    metadata_csv = (project_root / args.metadata_csv).resolve()
    checkpoint_dir = (project_root / args.checkpoint_dir).resolve()
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    frame = load_clean_metadata(metadata_csv, project_root=project_root)
    split = build_train_val_split(frame, val_size=args.val_size, seed=args.seed)

    weights = ResNet18_Weights.IMAGENET1K_V1
    normalize = weights.transforms()
    image_size = args.image_size

    train_transform = v2.Compose(
        [
            v2.Resize((image_size, image_size)),
            v2.RandomHorizontalFlip(p=0.5),
            v2.RandomRotation(degrees=10),
            v2.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            v2.ToImage(),
            v2.ToDtype(torch.float32, scale=True),
            normalize,
        ]
    )
    val_transform = v2.Compose(
        [
            v2.Resize((image_size, image_size)),
            v2.ToImage(),
            v2.ToDtype(torch.float32, scale=True),
            normalize,
        ]
    )

    train_dataset = FashionMultiTaskDataset(split.train, transform=train_transform)
    val_dataset = FashionMultiTaskDataset(split.val, transform=val_transform)

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = MultiTaskResNet18(pretrained=True).to(device)
    if args.freeze_backbone:
        for param in model.backbone.parameters():
            param.requires_grad = False

    gender_criterion = nn.CrossEntropyLoss()
    sleeve_criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )

    print(f"Using device: {device}")
    print(f"Total samples: {len(frame)} (train={len(split.train)}, val={len(split.val)})")

    history: list[EpochMetrics] = []
    best_score = -1.0
    best_path = checkpoint_dir / "best_multitask_resnet18.pt"

    for epoch in range(1, args.epochs + 1):
        train_loss, train_gender_acc, train_sleeve_acc = run_epoch(
            model,
            train_loader,
            gender_criterion=gender_criterion,
            sleeve_criterion=sleeve_criterion,
            optimizer=optimizer,
            device=device,
        )
        with torch.no_grad():
            val_loss, val_gender_acc, val_sleeve_acc = run_epoch(
                model,
                val_loader,
                gender_criterion=gender_criterion,
                sleeve_criterion=sleeve_criterion,
                optimizer=None,
                device=device,
            )

        val_avg_acc = (val_gender_acc + val_sleeve_acc) / 2.0
        metrics = EpochMetrics(
            epoch=epoch,
            train_loss=train_loss,
            val_loss=val_loss,
            train_gender_acc=train_gender_acc,
            train_sleeve_acc=train_sleeve_acc,
            val_gender_acc=val_gender_acc,
            val_sleeve_acc=val_sleeve_acc,
            val_avg_acc=val_avg_acc,
        )
        history.append(metrics)

        print(
            f"Epoch {epoch:02d}/{args.epochs} | "
            f"train_loss={train_loss:.4f} val_loss={val_loss:.4f} | "
            f"train_gender={train_gender_acc:.3f} train_sleeve={train_sleeve_acc:.3f} | "
            f"val_gender={val_gender_acc:.3f} val_sleeve={val_sleeve_acc:.3f}"
        )

        if val_avg_acc > best_score:
            best_score = val_avg_acc
            torch.save(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "model_name": "multitask_resnet18",
                    "val_avg_acc": best_score,
                    "state_dict": model.state_dict(),
                    "args": vars(args),
                },
                best_path,
            )

    history_path = checkpoint_dir / "training_history.csv"
    pd.DataFrame([asdict(row) for row in history]).to_csv(history_path, index=False)

    final_metrics = {
        "best_val_avg_acc": best_score,
        "best_checkpoint": str(best_path),
        "history_csv": str(history_path),
    }
    metrics_path = checkpoint_dir / "final_metrics.json"
    metrics_path.write_text(json.dumps(final_metrics, indent=2), encoding="utf-8")

    print("\nTraining complete.")
    print(f"Best checkpoint: {best_path}")
    print(f"History CSV:     {history_path}")
    print(f"Metrics JSON:    {metrics_path}")


if __name__ == "__main__":
    main()
