import torch
from config import BATCH_SIZE, DROPOUT_P, LR, N_EPOCHS, PATH_MODEL_TO_RESUME, PATH_TO_SAVE_RESULTS, RANDOM_SEED, RESUME_EPOCH, USE_RAVDESS_ONLY, AUDIO_METADATA_RAVDESS_CSV, AUDIO_METADATA_ALL_CSV, AUDIO_RAVDESS_FILES_DIR, AUDIO_FILES_DIR, REG, RESUME_TRAINING, USE_WANDB, NUM_CLASSES, LIMIT, BALANCE_DATASET, PRELOAD_AUDIO_FILES, SCALE_AUDIO_FILES, NUM_MFCC, LSTM_HIDDEN_SIZE, LSTM_NUM_LAYERS, USE_POSITIVE_NEGATIVE_LABELS
from dataloaders.voice_custom_dataloader import RAVDESSDataLoader
from models.AudioNetCL import AudioNet_CNN_LSTM as AudioNetCL
from train.loops.train_loop import train_eval_loop
from utils.utils import set_seed, select_device

def main():
    set_seed(RANDOM_SEED)
    device = select_device()
    ravdess_dataloader = RAVDESSDataLoader(csv_file=AUDIO_METADATA_RAVDESS_CSV if USE_RAVDESS_ONLY else AUDIO_METADATA_ALL_CSV,
                                           audio_files_dir=AUDIO_RAVDESS_FILES_DIR if USE_RAVDESS_ONLY else AUDIO_FILES_DIR,
                                           batch_size=BATCH_SIZE,
                                           seed=RANDOM_SEED,
                                           limit=LIMIT,
                                           balance_dataset=BALANCE_DATASET,
                                           preload_audio_files=PRELOAD_AUDIO_FILES,
                                           scale_audio_files=SCALE_AUDIO_FILES,
                                           use_positive_negative_labels=USE_POSITIVE_NEGATIVE_LABELS
                                        )
    train_loader = ravdess_dataloader.get_train_dataloader()
    val_loader = ravdess_dataloader.get_val_dataloader()
    model = AudioNetCL(num_classes=NUM_CLASSES, num_mfcc=NUM_MFCC).to(device)
    if RESUME_TRAINING:
        model.load_state_dict(torch.load(
            f"{PATH_TO_SAVE_RESULTS}/{PATH_MODEL_TO_RESUME}/models/mi_project_{RESUME_EPOCH}.pt"))
    optimizer = torch.optim.AdamW(model.parameters(),
                                  lr=LR,
                                  weight_decay=REG)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=N_EPOCHS,
        eta_min=1e-2,
        verbose=True)
    criterion = torch.nn.CrossEntropyLoss()

    if PRELOAD_AUDIO_FILES and SCALE_AUDIO_FILES:
        scaler = ravdess_dataloader.scaler

    config = {
        "architecture": "AudioNetCL",
        "scope": "AudioNet",
        "learning_rate": LR,
        "epochs": N_EPOCHS,
        "reg": REG,
        "batch_size": BATCH_SIZE,
        "lstm_hidden_size": LSTM_HIDDEN_SIZE,
        "lstm_num_layers": LSTM_NUM_LAYERS,
        "num_classes": NUM_CLASSES,
        "num_mfcc": NUM_MFCC,
        "dataset": "RAVDESS" if USE_RAVDESS_ONLY else "ALL_VOICE_DATASETS",
        "optimizer": "AdamW",
        "resumed": RESUME_TRAINING,
        "use_wandb": USE_WANDB,
        "balance_dataset": BALANCE_DATASET,
        "preload_audio_files": PRELOAD_AUDIO_FILES,
        "scale_audio_files": SCALE_AUDIO_FILES,
        "limit": LIMIT,
        "dropout_p": DROPOUT_P
    }

    train_eval_loop(device=device,
                    train_loader=train_loader,
                    val_loader=val_loader,
                    model=model,
                    config=config,
                    optimizer=optimizer,
                    scheduler=scheduler,
                    criterion=criterion,
                    scaler=scaler,
                    resume=RESUME_TRAINING)

if __name__ == "__main__":
    main()