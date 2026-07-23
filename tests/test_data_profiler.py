import pandas as pd

from src.tools.data_profiler import (
    dataset_hash,
    detect_column_roles,
    profile_dataset,
    validate_config_columns,
)


def test_dataset_hash_is_stable():
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "test": [0, 1, 1],
        "purchase": [0, 1, 0],
    })

    first_hash = dataset_hash(df)
    second_hash = dataset_hash(df)

    assert first_hash == second_hash
    assert isinstance(first_hash, str)


def test_detect_column_roles_identifies_binary_and_id_columns():
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "test": [0, 1, 1],
        "purchase": [0, 1, 0],
        "income": [50, 60, 70],
        "site": ["A", "B", "A"],
    })

    roles = detect_column_roles(df)

    assert "id" in roles["possible_id_columns"]
    assert "test" in roles["binary_columns"]
    assert "purchase" in roles["binary_columns"]
    assert "income" in roles["numeric_columns"]
    assert "site" in roles["categorical_columns"]


def test_validate_config_columns_flags_missing_columns():
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "test": [0, 1, 1],
        "purchase": [0, 1, 0],
    })

    config = {
        "outcome_col": "purchase",
        "treatment_col": "test",
        "unit_id_col": "id",
        "covariates": ["income"],
        "segment_cols": [],
    }

    validation = validate_config_columns(df, config)

    assert validation["config_valid"] is False
    assert "income" in validation["missing_columns"]


def test_profile_dataset_returns_expected_structure():
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "test": [0, 1, 1],
        "purchase": [0, 1, 0],
    })

    profile = profile_dataset(df)

    assert profile["n_rows"] == 3
    assert profile["n_columns"] == 3
    assert "dataset_hash" in profile
    assert "role_summary" in profile
