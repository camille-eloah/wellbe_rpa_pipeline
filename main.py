from src.pipeline import run_pipeline


if __name__ == "__main__":
    summary = run_pipeline(load_to_database=True)
    print(summary)
