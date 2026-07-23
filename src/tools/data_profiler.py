"""
ClaimCheck Data Profiler

This module inspects a dataset before method selection.

Purpose:
- summarize dataset shape and columns
- detect missing values
- infer basic column roles
- identify binary columns
- validate user-provided configuration
- generate a dataset hash for auditability
"""

from typing import Any, Dict, List, Optional
import hashlib

import pandas as pd


def dataset_hash(df: pd.DataFrame) -> str:
    """
    Create a reproducible hash of the dataset contents.

    This supports auditability by recording which dataset was reviewed.
    """
    hashed = pd.util.hash_pandas_object(df, index=True).values
    return hashlib.sha256(hashed).hexdigest()


def is_binary_series(series: pd.Series) -> bool:
    """
    Check whether a column contains exactly two non-null unique values.
    """
    non_null_values = series.dropna().unique()
    return len(non_null_values) == 2


def detect_column_roles(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Infer basic column roles from data types and value patterns.

    This is intentionally conservative. It does not make business decisions;
    it only helps later agents and tools understand the dataset structure.
    """
    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_columns = df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    binary_columns = [
        col for col in df.columns
        if is_binary_series(df[col])
    ]

    possible_id_columns = [
        col for col in df.columns
        if col.lower() in ["id", "user_id", "customer_id", "account_id", "unit_id"]
        or col.lower().endswith("_id")
    ]

    possible_time_columns = [
        col for col in df.columns
        if any(token in col.lower() for token in ["date", "time", "month", "week", "day"])
    ]

    return {
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "binary_columns": binary_columns,
        "possible_id_columns": possible_id_columns,
        "possible_time_columns": possible_time_columns,
    }


def validate_config_columns(
    df: pd.DataFrame,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate whether configured columns exist in the dataset.

    Expected config keys may include:
    - outcome_col
    - treatment_col
    - group_col
    - time_col
    - unit_id_col
    - covariates
    - segment_cols
    """
    required_single_columns = [
        "outcome_col",
        "treatment_col",
        "group_col",
        "time_col",
        "unit_id_col",
    ]

    missing_columns = []
    present_columns = []

    for key in required_single_columns:
        col = config.get(key)
        if col is None:
            continue
        if col in df.columns:
            present_columns.append(col)
        else:
            missing_columns.append(col)

    for key in ["covariates", "segment_cols"]:
        columns = config.get(key) or []
        for col in columns:
            if col in df.columns:
                present_columns.append(col)
            else:
                missing_columns.append(col)

    return {
        "config_valid": len(missing_columns) == 0,
        "present_columns": sorted(list(set(present_columns))),
        "missing_columns": sorted(list(set(missing_columns))),
    }


def profile_dataset(
    df: pd.DataFrame,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Produce a structured dataset profile for ClaimCheck.

    The profile is used by:
    - Fisher Method Selection Agent
    - deterministic validation tools
    - audit logger
    - Streamlit UI
    """
    role_summary = detect_column_roles(df)
    missing_summary = df.isna().sum().to_dict()

    profile = {
        "dataset_hash": dataset_hash(df),
        "n_rows": int(df.shape[0]),
        "n_columns": int(df.shape[1]),
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": {
            col: int(count)
            for col, count in missing_summary.items()
        },
        "missing_value_total": int(df.isna().sum().sum()),
        "role_summary": role_summary,
    }

    if config is not None:
        profile["config_validation"] = validate_config_columns(df, config)

    return profile


def summarize_dataset_profile(profile: Dict[str, Any]) -> str:
    """
    Create a concise human-readable summary of the dataset profile.
    """
    role_summary = profile.get("role_summary", {})

    return (
        f"Dataset contains {profile.get('n_rows')} rows and "
        f"{profile.get('n_columns')} columns. "
        f"Detected {len(role_summary.get('numeric_columns', []))} numeric columns, "
        f"{len(role_summary.get('categorical_columns', []))} categorical columns, "
        f"and {len(role_summary.get('binary_columns', []))} binary columns. "
        f"Total missing values: {profile.get('missing_value_total')}."
    )
