"""
Enhanced Insight Generation Layer.
Converts EDA results into structured, actionable InsightItems.
Each insight has a title, description, why it matters, and a suggested action.
Uses ONLY rule-based logic (no ML / no LLM).
"""
from __future__ import annotations
from models.schemas import DatasetMetrics, Correlation, Distribution, InsightItem


def generate_insights(
    metrics: DatasetMetrics,
    correlations: list[Correlation],
    distributions: list[Distribution],
) -> list[InsightItem]:
    """
    Analyze EDA results and produce a list of structured InsightItems.
    Each insight is actionable and categorized by severity.
    """
    insights: list[InsightItem] = []

    # ── Missing values insights ──────────────────────────────────
    if metrics.missingPercent == 0:
        insights.append(InsightItem(
            title="Complete Dataset",
            description="No missing values detected — dataset is fully complete.",
            why_it_matters="Complete datasets require no imputation, reducing risk of introduced bias and preserving original data fidelity.",
            suggested_action="No action needed. Proceed directly to feature engineering or modeling.",
            severity="info",
            category="missing",
        ))
    elif metrics.missingPercent <= 2:
        insights.append(InsightItem(
            title="Minimal Missing Values",
            description=f"Only {metrics.missingPercent}% of values are missing — minimal imputation needed.",
            why_it_matters="Low missing rates have negligible impact on model performance. Simple imputation strategies will work well.",
            suggested_action="Use mean/median imputation for numeric columns, or mode imputation for categorical columns.",
            severity="info",
            category="missing",
        ))
    elif metrics.missingPercent <= 10:
        insights.append(InsightItem(
            title="Moderate Missing Values",
            description=f"{metrics.missingPercent}% of values are missing — consider imputation strategies.",
            why_it_matters="Missing data at this level can affect model accuracy if not handled properly. Pattern-based approaches may be needed.",
            suggested_action="Apply KNN or iterative imputation for better results. Avoid dropping rows unless the dataset is very large.",
            severity="warning",
            category="missing",
        ))
    else:
        insights.append(InsightItem(
            title="High Missing Values",
            description=f"{metrics.missingPercent}% of values are missing — significant data cleaning required.",
            why_it_matters="High missing rates can severely distort model training, introduce bias, and reduce prediction reliability.",
            suggested_action="Use iterative (MICE) imputation or KNN imputation. Consider dropping columns with >50% missing. Investigate why data is missing (MCAR/MAR/MNAR).",
            severity="critical",
            category="missing",
        ))

    # Per-column missing value alerts (top offenders only)
    high_missing_cols = []
    for col in metrics.columnTypes:
        if col.nullCount > 0 and metrics.rows > 0:
            pct = round(col.nullCount / metrics.rows * 100, 1)
            if pct > 30:
                high_missing_cols.append((col.name, pct))
            elif pct > 10:
                insights.append(InsightItem(
                    title=f"Missing Values in '{col.name}'",
                    description=f"Column '{col.name}' has {pct}% missing values ({col.nullCount:,} nulls out of {metrics.rows:,} rows).",
                    why_it_matters=f"Missing values in a single column can cause issues if that column is important for prediction.",
                    suggested_action=f"Apply column-specific imputation (median for numeric, mode for categorical) or use KNN imputation to leverage other features.",
                    severity="warning",
                    category="missing",
                ))

    if high_missing_cols:
        col_list = ", ".join(f"'{c[0]}' ({c[1]}%)" for c in high_missing_cols[:5])
        insights.append(InsightItem(
            title=f"Critically High Missing Columns ({len(high_missing_cols)})",
            description=f"These columns have >30% missing values: {col_list}.",
            why_it_matters="Columns with very high missing rates may not carry enough signal. Imputing them adds noise.",
            suggested_action="Consider dropping columns with >50% missing. For 30-50% missing, use advanced imputation (iterative/KNN) or flag them as unreliable features.",
            severity="critical",
            category="missing",
        ))

    # ── Duplicate insights ───────────────────────────────────────
    if metrics.duplicatePercent == 0:
        insights.append(InsightItem(
            title="No Duplicate Rows",
            description="No duplicate rows detected — every record is unique.",
            why_it_matters="Unique rows ensure each observation contributes independently to model training.",
            suggested_action="No action needed.",
            severity="info",
            category="duplicates",
        ))
    elif metrics.duplicatePercent <= 1:
        insights.append(InsightItem(
            title="Minimal Duplicates",
            description=f"Only {metrics.duplicatePercent}% duplicate rows — negligible impact.",
            why_it_matters="A tiny fraction of duplicates is common and unlikely to bias results.",
            suggested_action="Optionally remove duplicates for cleanliness, but impact is minimal.",
            severity="info",
            category="duplicates",
        ))
    elif metrics.duplicatePercent <= 5:
        insights.append(InsightItem(
            title="Moderate Duplicate Rows",
            description=f"{metrics.duplicatePercent}% duplicate rows detected — review for unintentional data replication.",
            why_it_matters="Duplicates can inflate certain class frequencies and bias model evaluation metrics.",
            suggested_action="Remove duplicate rows before splitting into train/test to prevent data leakage.",
            severity="warning",
            category="duplicates",
        ))
    else:
        insights.append(InsightItem(
            title="High Duplicate Rows",
            description=f"{metrics.duplicatePercent}% duplicate rows — significant duplication detected.",
            why_it_matters="High duplication can severely bias model training, inflating accuracy on repeated samples and causing overfitting.",
            suggested_action="Remove all duplicate rows immediately. Investigate the data source — this level of duplication often indicates a data collection or joining error.",
            severity="critical",
            category="duplicates",
        ))

    # ── Size insights ────────────────────────────────────────────
    if metrics.rows < 100:
        insights.append(InsightItem(
            title="Very Small Dataset",
            description=f"Only {metrics.rows:,} rows — may not support complex models.",
            why_it_matters="Small datasets are prone to overfitting and unreliable cross-validation. Statistical patterns may not generalize.",
            suggested_action="Use simple models (Logistic Regression, Decision Trees), aggressive cross-validation (Leave-One-Out), or consider data augmentation (SMOTE for classification).",
            severity="warning",
            category="size",
        ))
    elif metrics.rows < 1000:
        insights.append(InsightItem(
            title="Moderate Dataset Size",
            description=f"{metrics.rows:,} rows, {metrics.columns} columns — suitable for simpler models.",
            why_it_matters="Enough data for basic ML models but may struggle with deep learning or high-dimensional problems.",
            suggested_action="Ensemble methods (Random Forest, XGBoost) work well at this size. Use stratified k-fold cross-validation.",
            severity="info",
            category="size",
        ))
    elif metrics.rows < 10000:
        insights.append(InsightItem(
            title="Good Dataset Size",
            description=f"{metrics.rows:,} rows, {metrics.columns} columns — supports a wide range of ML models.",
            why_it_matters="This is a comfortable size for most classical ML models and even some simpler neural networks.",
            suggested_action="Proceed with model selection. Consider gradient boosting methods for best performance.",
            severity="info",
            category="size",
        ))
    else:
        insights.append(InsightItem(
            title="Large Dataset",
            description=f"{metrics.rows:,} rows, {metrics.columns} columns — excellent for complex models.",
            why_it_matters="Large datasets support deep learning, complex feature interactions, and robust evaluation.",
            suggested_action="Consider gradient boosting (XGBoost, LightGBM) or neural networks. Use stratified sampling for faster experimentation.",
            severity="info",
            category="size",
        ))

    # ── Low-variance / low-cardinality columns ───────────────────
    single_value_cols = []
    potential_binary = []
    numeric_low_card = []

    for col in metrics.columnTypes:
        if col.uniqueCount == 1:
            single_value_cols.append(col.name)
        elif col.uniqueCount == 2 and col.type != "boolean":
            potential_binary.append(col.name)
        elif col.type == "number" and col.uniqueCount <= 5:
            numeric_low_card.append((col.name, col.uniqueCount))

    if single_value_cols:
        insights.append(InsightItem(
            title=f"Constant Columns ({len(single_value_cols)})",
            description=f"Columns with only 1 unique value: {', '.join(repr(c) for c in single_value_cols[:5])}.",
            why_it_matters="Constant columns provide zero information gain to any model. They add computational overhead without benefit.",
            suggested_action="Drop these columns before training. They cannot contribute to predictions.",
            severity="critical",
            category="column",
        ))

    if potential_binary:
        insights.append(InsightItem(
            title=f"Potential Binary Features ({len(potential_binary)})",
            description=f"Columns with only 2 unique values: {', '.join(repr(c) for c in potential_binary[:5])}.",
            why_it_matters="Binary features can be powerful predictors. Ensure they are properly encoded (0/1) for modeling.",
            suggested_action="Verify these are intentionally binary. Encode as 0/1 if they aren't already.",
            severity="info",
            category="column",
        ))

    if numeric_low_card:
        cols_desc = ", ".join(f"'{c[0]}' ({c[1]} values)" for c in numeric_low_card[:5])
        insights.append(InsightItem(
            title=f"Low-Cardinality Numeric Columns ({len(numeric_low_card)})",
            description=f"Numeric columns with very few unique values: {cols_desc}.",
            why_it_matters="These may actually be categorical features encoded as numbers. Treating them as continuous can mislead models.",
            suggested_action="Consider converting to categorical type or using one-hot encoding for these columns.",
            severity="info",
            category="column",
        ))

    # ── High-cardinality categorical columns ─────────────────────
    high_card_cols = []
    for col in metrics.columnTypes:
        if col.type == "string" and metrics.rows > 0:
            cardinality_ratio = col.uniqueCount / metrics.rows
            if cardinality_ratio > 0.9:
                high_card_cols.append((col.name, col.uniqueCount))

    if high_card_cols:
        cols_desc = ", ".join(f"'{c[0]}' ({c[1]:,} unique)" for c in high_card_cols[:5])
        insights.append(InsightItem(
            title=f"High-Cardinality Identifiers ({len(high_card_cols)})",
            description=f"Columns that appear to be IDs or unique identifiers: {cols_desc}.",
            why_it_matters="ID-like columns cause massive feature explosion with one-hot encoding and don't generalize. They can cause data leakage.",
            suggested_action="Drop these columns before modeling. If needed for joins, store separately.",
            severity="warning",
            category="column",
        ))

    # ── Correlation insights ─────────────────────────────────────
    very_strong = []
    strong = []
    moderate = []

    for corr in correlations:
        abs_val = abs(corr.value)
        direction = "positive" if corr.value > 0 else "negative"
        if abs_val >= 0.9:
            very_strong.append((corr, direction))
        elif abs_val >= 0.7:
            strong.append((corr, direction))
        elif abs_val >= 0.5:
            moderate.append((corr, direction))

    if very_strong:
        pairs = ", ".join(f"'{c.column1}' ↔ '{c.column2}' (r={c.value:.2f})" for c, _ in very_strong[:3])
        insights.append(InsightItem(
            title=f"Very Strong Correlations ({len(very_strong)} pairs)",
            description=f"Near-perfect correlations detected: {pairs}.",
            why_it_matters="Highly correlated features provide redundant information, cause multicollinearity in linear models, and inflate coefficients.",
            suggested_action="Remove one feature from each highly correlated pair. Keep the one with more domain relevance or less missing data.",
            severity="critical",
            category="correlation",
        ))

    if strong:
        pairs = ", ".join(f"'{c.column1}' ↔ '{c.column2}' (r={c.value:.2f})" for c, _ in strong[:3])
        insights.append(InsightItem(
            title=f"Strong Correlations ({len(strong)} pairs)",
            description=f"Strong correlations found: {pairs}.",
            why_it_matters="Strong correlations can indicate useful feature relationships but may also hint at redundancy.",
            suggested_action="Consider using PCA or VIF analysis to handle multicollinearity. Tree-based models are less affected.",
            severity="warning",
            category="correlation",
        ))

    if moderate:
        insights.append(InsightItem(
            title=f"Moderate Correlations ({len(moderate)} pairs)",
            description=f"{len(moderate)} feature pairs show moderate correlation (|r| between 0.5 and 0.7).",
            why_it_matters="Moderate correlations can indicate genuine feature relationships useful for prediction.",
            suggested_action="These are generally fine. Monitor during model training — feature importance scores will clarify their value.",
            severity="info",
            category="correlation",
        ))

    # ── Distribution insights ────────────────────────────────────
    skewed_cols = []
    for dist in distributions:
        if len(dist.bins) >= 2:
            counts = [b.get("count", 0) if isinstance(b, dict) else 0 for b in dist.bins]
            if counts:
                max_count = max(counts)
                min_count = min(counts)
                if max_count > 0 and min_count / max_count < 0.1:
                    skewed_cols.append(dist.column)

    if skewed_cols:
        insights.append(InsightItem(
            title=f"Skewed Distributions ({len(skewed_cols)} columns)",
            description=f"Highly skewed distributions detected in: {', '.join(repr(c) for c in skewed_cols[:5])}.",
            why_it_matters="Skewed features can bias models that assume normal distributions (linear regression, SVM). Outliers have disproportionate influence.",
            suggested_action="Apply Yeo-Johnson or Box-Cox power transforms to normalize these distributions. Log transform works for strictly positive values.",
            severity="warning",
            category="distribution",
        ))

    # ── Column diversity insight ─────────────────────────────────
    type_counts: dict[str, int] = {}
    for c in metrics.columnTypes:
        type_counts[c.type] = type_counts.get(c.type, 0) + 1

    has_numeric = "number" in type_counts
    has_categorical = "string" in type_counts
    has_date = "date" in type_counts

    if has_numeric and has_categorical:
        insights.append(InsightItem(
            title="Good Feature Diversity",
            description=f"Dataset has a mix of {type_counts.get('number', 0)} numeric, {type_counts.get('string', 0)} categorical"
                        + (f", and {type_counts['date']} date" if has_date else "") + " columns.",
            why_it_matters="Feature diversity enables richer models. Categorical features capture group effects while numeric features capture magnitude.",
            suggested_action="Encode categorical features appropriately (one-hot for low cardinality, target encoding for high cardinality).",
            severity="info",
            category="column",
        ))
    elif not has_numeric and has_categorical:
        insights.append(InsightItem(
            title="All Categorical Features",
            description="Dataset contains only categorical (text) columns — no numeric features detected.",
            why_it_matters="Many ML models require numeric input. Encoding all features adds dimensionality.",
            suggested_action="Apply label encoding or one-hot encoding. Consider NLP techniques if columns contain free text.",
            severity="warning",
            category="column",
        ))

    return insights
