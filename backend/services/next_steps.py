"""
"What To Do Next" Recommendation Engine.
Analyzes dataset metrics, insights, and ML recommendations
to produce an ordered list of actionable next steps.
"""
from __future__ import annotations
import logging
from models.schemas import (
    DatasetMetrics, InsightItem, MLRecommendation,
    BiasWarning, NextStep, ScoreBreakdown,
)

logger = logging.getLogger(__name__)


def generate_next_steps(
    metrics: DatasetMetrics,
    insights: list[InsightItem],
    ml_recommendation: MLRecommendation,
    bias_warnings: list[BiasWarning],
    score_breakdown: ScoreBreakdown | None = None,
    quality_score: float = 0.0,
) -> list[NextStep]:
    """
    Generate an ordered list of actionable next steps.
    Steps are priority-ordered — most critical actions first.
    """
    steps: list[NextStep] = []
    order = 1

    # ── Critical preprocessing steps (based on data quality) ─────

    # 1. Handle missing values (if significant)
    if metrics.missingPercent > 5:
        steps.append(NextStep(
            order=order,
            title="Handle Missing Values",
            description=(
                f"Your dataset has {metrics.missingPercent}% missing values. "
                "Use the preprocessing panel to apply KNN or iterative imputation for best results."
            ),
            action_type="preprocess",
            action_key="handle_missing",
            is_critical=metrics.missingPercent > 15,
        ))
        order += 1
    elif metrics.missingPercent > 0:
        steps.append(NextStep(
            order=order,
            title="Clean Missing Values",
            description=(
                f"Only {metrics.missingPercent}% missing — a quick median/mode fill will work. "
                "Use the preprocessing panel to apply this fix."
            ),
            action_type="preprocess",
            action_key="handle_missing",
            is_critical=False,
        ))
        order += 1

    # 2. Remove duplicates (if present)
    if metrics.duplicatePercent > 2:
        steps.append(NextStep(
            order=order,
            title="Remove Duplicate Rows",
            description=(
                f"{metrics.duplicatePercent}% duplicate rows detected. "
                "Remove them to prevent data leakage and biased evaluation."
            ),
            action_type="preprocess",
            action_key="remove_duplicates",
            is_critical=metrics.duplicatePercent > 10,
        ))
        order += 1

    # 3. Drop constant columns
    constant_cols = [c for c in metrics.columnTypes if c.uniqueCount <= 1]
    if constant_cols:
        steps.append(NextStep(
            order=order,
            title="Drop Constant Columns",
            description=(
                f"{len(constant_cols)} column(s) have only 1 unique value and provide no information. "
                "Remove them to simplify your model."
            ),
            action_type="preprocess",
            action_key="drop_low_variance",
            is_critical=False,
        ))
        order += 1

    # 4. Handle correlated features
    has_strong_corr = any(
        i.category == "correlation" and i.severity == "critical"
        for i in insights
    )
    if has_strong_corr:
        steps.append(NextStep(
            order=order,
            title="Remove Highly Correlated Features",
            description=(
                "Very strong correlations (>0.9) detected between features. "
                "Remove redundant features to reduce multicollinearity."
            ),
            action_type="preprocess",
            action_key="remove_correlated",
            is_critical=False,
        ))
        order += 1

    # 5. Handle skewness
    has_skew = any(
        i.category == "distribution" and i.severity in ("warning", "critical")
        for i in insights
    )
    if has_skew:
        steps.append(NextStep(
            order=order,
            title="Fix Skewed Distributions",
            description=(
                "Some features have highly skewed distributions. "
                "Apply Yeo-Johnson power transform to improve normality."
            ),
            action_type="preprocess",
            action_key="handle_skewness",
            is_critical=False,
        ))
        order += 1

    # 6. Handle bias/imbalance
    class_imbalance = [b for b in bias_warnings if b.type == "class_imbalance"]
    if class_imbalance:
        steps.append(NextStep(
            order=order,
            title="Address Class Imbalance",
            description=(
                f"{class_imbalance[0].description} "
                "Consider SMOTE oversampling or adjusting class weights in your model."
            ),
            action_type="info",
            is_critical=class_imbalance[0].severity == "high",
        ))
        order += 1

    # 7. Handle outliers
    outlier_warnings = [b for b in bias_warnings if b.type == "outlier_heavy"]
    if outlier_warnings:
        steps.append(NextStep(
            order=order,
            title="Handle Outliers",
            description=(
                "Some columns have significant outlier percentages. "
                "Use IQR-based removal or robust scaling to reduce their impact."
            ),
            action_type="preprocess",
            action_key="remove_outliers",
            is_critical=False,
        ))
        order += 1

    # ── Modeling steps ───────────────────────────────────────────

    # 8. Normalize features
    numeric_count = sum(1 for c in metrics.columnTypes if c.type == "number")
    if numeric_count >= 2:
        steps.append(NextStep(
            order=order,
            title="Normalize Features",
            description=(
                f"Apply robust scaling to {numeric_count} numeric features. "
                "This ensures all features contribute equally to model training."
            ),
            action_type="preprocess",
            action_key="normalize",
            is_critical=False,
        ))
        order += 1

    # 9. Encode categoricals
    cat_count = sum(1 for c in metrics.columnTypes if c.type == "string")
    if cat_count > 0:
        steps.append(NextStep(
            order=order,
            title="Encode Categorical Features",
            description=(
                f"Convert {cat_count} categorical columns to numeric format. "
                "Use one-hot encoding for low-cardinality, label encoding for high-cardinality."
            ),
            action_type="preprocess",
            action_key="encode_categorical",
            is_critical=False,
        ))
        order += 1

    # 10. Split data
    steps.append(NextStep(
        order=order,
        title="Split into Train/Test Sets",
        description=(
            "Split your cleaned dataset into training (80%) and test (20%) sets. "
            "Use stratified splitting for classification tasks."
        ),
        action_type="model",
        is_critical=False,
    ))
    order += 1

    # 11. Train model
    if ml_recommendation and ml_recommendation.task:
        models = ", ".join(ml_recommendation.suggestedModels[:3])
        steps.append(NextStep(
            order=order,
            title=f"Train a {ml_recommendation.task.replace('-', ' ').title()} Model",
            description=(
                f"Based on your data, we recommend: {models}. "
                f"{'Target column: ' + ml_recommendation.targetColumn + '.' if ml_recommendation.targetColumn else ''}"
            ),
            action_type="model",
            is_critical=False,
        ))
        order += 1

    # 12. Evaluate
    steps.append(NextStep(
        order=order,
        title="Evaluate Model Performance",
        description=(
            "Use cross-validation and appropriate metrics. "
            "For classification: F1-score, AUC-ROC. For regression: RMSE, R². "
            "For clustering: silhouette score."
        ),
        action_type="info",
        is_critical=False,
    ))

    return steps
