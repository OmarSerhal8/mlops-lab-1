import argparse
from pathlib import Path

import mlflow
import mlflow.pytorch
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


# ============================================================
# 1. READ COMMAND-LINE ARGUMENTS
# ============================================================

def parse_args():
    parser = argparse.ArgumentParser()

    # Which dataset version we want to use
    parser.add_argument(
        "--dataset",
        choices=["mini", "processed"],
        default="mini",
    )

    # Number of complete passes through the training dataset
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
    )

    # Learning rate used by Adam
    parser.add_argument(
        "--lr",
        type=float,
        default=0.001,
    )

    # Number of images processed at the same time
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
    )

    return parser.parse_args()


# ============================================================
# 2. LOAD THE DATASETS
# ============================================================

def create_dataloaders(dataset_name, batch_size):

    # Select mini or full processed dataset
    if dataset_name == "mini":
        data_root = Path("data/food11_processed_mini")
    else:
        data_root = Path("data/food11_processed")

    # Preprocessing applied when an image is loaded
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),

        # Standard ImageNet normalization used with pretrained ResNet18
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    # ImageFolder automatically uses subfolder names as classes
    train_dataset = datasets.ImageFolder(
        data_root / "training",
        transform=transform,
    )

    val_dataset = datasets.ImageFolder(
        data_root / "validation",
        transform=transform,
    )

    test_dataset = datasets.ImageFolder(
        data_root / "evaluation",
        transform=transform,
    )

    # DataLoaders divide the datasets into batches
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
    )

    return train_loader, val_loader, test_loader


# ============================================================
# 3. CREATE THE MODEL
# ============================================================

def create_model():

    # Load pretrained ResNet18 weights
    weights = models.ResNet18_Weights.DEFAULT
    model = models.resnet18(weights=weights)

    # ResNet18 normally has:
    # 512 features -> 1000 ImageNet classes
    #
    # Food-11 has only 11 classes, so replace the final layer.
    num_features = model.fc.in_features

    model.fc = nn.Linear(
        num_features,
        11,
    )

    return model


# ============================================================
# 4. TRAIN FOR ONE EPOCH
# ============================================================

def train_one_epoch(model, loader, criterion, optimizer, device):

    # Put the model in training mode
    model.train()

    total_loss = 0.0

    # Process one batch at a time
    for images, labels in loader:

        # Move images and labels to GPU/CPU
        images = images.to(device)
        labels = labels.to(device)

        # Remove gradients from the previous batch
        optimizer.zero_grad()

        # Forward pass
        outputs = model(images)

        # Calculate classification loss
        loss = criterion(outputs, labels)

        # Backpropagation: calculate gradients
        loss.backward()

        # Adam updates the model parameters
        optimizer.step()

        total_loss += loss.item()

    # Average loss over all batches
    average_loss = total_loss / len(loader)

    return average_loss


# ============================================================
# 5. VALIDATE / TEST THE MODEL
# ============================================================

def evaluate(model, loader, criterion, device):

    # Evaluation mode: no training behavior
    model.eval()

    total_loss = 0.0
    correct = 0
    total = 0

    # We don't need gradients during evaluation
    with torch.no_grad():

        for images, labels in loader:

            images = images.to(device)
            labels = labels.to(device)

            # Forward pass only
            outputs = model(images)

            loss = criterion(outputs, labels)

            total_loss += loss.item()

            # Choose the class with the largest output score
            predictions = outputs.argmax(dim=1)

            # Count correct predictions
            correct += (predictions == labels).sum().item()

            # Count total images
            total += labels.size(0)

    average_loss = total_loss / len(loader)
    accuracy = correct / total

    return average_loss, accuracy


# ============================================================
# 6. MAIN PROGRAM
# ============================================================

def main():

    # Read --dataset, --epochs, --lr and --batch-size
    args = parse_args()

    # Use NVIDIA GPU if CUDA is available; otherwise use CPU
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print(f"Using device: {device}")

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    train_loader, val_loader, test_loader = create_dataloaders(
        args.dataset,
        args.batch_size,
    )

    # --------------------------------------------------------
    # Create ResNet18
    # --------------------------------------------------------

    model = create_model()

    # Move model to GPU or CPU
    model = model.to(device)

    # Multiclass classification loss
    criterion = nn.CrossEntropyLoss()

    # Adam optimizer
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=args.lr,
    )

    # --------------------------------------------------------
    # Configure MLflow
    # --------------------------------------------------------

    # Address of the MLflow tracking server
    mlflow.set_tracking_uri(
        "http://127.0.0.1:5000"
    )

    # Create/select the food11 experiment
    mlflow.set_experiment("food11")

    # --------------------------------------------------------
    # Start ONE MLflow run
    # --------------------------------------------------------

    with mlflow.start_run():

        # Parameters are fixed configuration values for this run
        mlflow.log_params({
            "dataset": args.dataset,
            "epochs": args.epochs,
            "lr": args.lr,
            "batch_size": args.batch_size,
            "model": "resnet18",
        })

        # ----------------------------------------------------
        # TRAINING LOOP
        # ----------------------------------------------------

        for epoch in range(args.epochs):

            # Train the model for one complete epoch
            train_loss = train_one_epoch(
                model,
                train_loader,
                criterion,
                optimizer,
                device,
            )

            # Evaluate on validation data
            val_loss, val_accuracy = evaluate(
                model,
                val_loader,
                criterion,
                device,
            )

            # Log metrics for this specific epoch
            mlflow.log_metric(
                "train_loss",
                train_loss,
                step=epoch,
            )

            mlflow.log_metric(
                "val_loss",
                val_loss,
                step=epoch,
            )

            mlflow.log_metric(
                "val_accuracy",
                val_accuracy,
                step=epoch,
            )

            print(
                f"Epoch {epoch + 1}/{args.epochs} "
                f"- train_loss: {train_loss:.4f} "
                f"- val_loss: {val_loss:.4f} "
                f"- val_accuracy: {val_accuracy:.4f}"
            )

        # ----------------------------------------------------
        # FINAL TEST
        # ----------------------------------------------------

        test_loss, test_accuracy = evaluate(
            model,
            test_loader,
            criterion,
            device,
        )

        print(f"Test accuracy: {test_accuracy:.4f}")

        # Test accuracy is a final metric
        mlflow.log_metric(
            "test_accuracy",
            test_accuracy,
        )

        # ----------------------------------------------------
        # SAVE TRAINED MODEL AS AN MLFLOW ARTIFACT
        # ----------------------------------------------------
        mlflow.pytorch.log_model(
    model,
    name="model",
    serialization_format="pickle",
)
        


# ============================================================
# 7. START THE PROGRAM
# ============================================================

if __name__ == "__main__":
    main()