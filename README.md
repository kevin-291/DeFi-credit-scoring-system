# DeFi Credit Scoring System for Aave V2 Protocol

## Overview

This project implements a comprehensive credit scoring system for DeFi users based on their transaction behavior on the Aave V2 protocol. The system analyzes wallet-level transaction patterns to assign credit scores between 0-1000, where higher scores indicate more reliable and responsible DeFi usage.

## Problem Statement

Traditional credit scoring doesn't apply to DeFi protocols where users interact pseudonymously through wallet addresses. This system addresses the need for:
- Risk assessment for lending protocols
- User behavior classification
- Credit worthiness evaluation based on on-chain activity
- Detection of bot-like or exploitative behavior

## Architecture & Methodology

### 1. Data Processing Pipeline

```
Raw Transaction Data (JSON) → Feature Engineering → Credit Scoring → ML Validation → Results Export
```

### 2. Core Components

#### **AaveCreditScorer Class** (`preprocess.py`)
- **Data Loading**: Processes raw transaction JSON files
- **Feature Engineering**: Extracts 25+ behavioral features
- **Rule-Based Scoring**: Calculates initial credit scores
- **Analysis & Categorization**: Provides risk category classification

#### **Machine Learning Validation** (`models.ipynb`)
- **Model Training**: Random Forest, XGBoost, CatBoost
- **Feature Importance**: Identifies key scoring factors
- **Performance Metrics**: RMSE, MAE, R² evaluation

#### **Visualization** (`plots.ipynb`)
- **Score Distribution**: Histogram analysis
- **Feature Correlations**: Heatmap visualizations
- **Prediction Accuracy**: Scatter plots

## Feature Engineering Strategy

### Transaction Behavior Features
- **Activity Metrics**: Total transactions, unique actions, asset diversity
- **Temporal Patterns**: Days active, transaction frequency, time-based behavior
- **Financial Metrics**: Volume, transaction sizes, volatility measures

### DeFi-Specific Features
- **Repayment Behavior**: Repay-to-borrow ratios (highest weight factor)
- **Deposit Patterns**: Deposit-to-borrow ratios, collateral behavior
- **Liquidation History**: Liquidation events and frequency
- **Asset Diversification**: Number of unique assets used

### Risk Indicators
- **Bot Detection**: Burst activity patterns, night activity ratios
- **Consistency Measures**: Transaction size variance, behavioral patterns
- **User Classification**: Regular vs. irregular usage patterns

## Credit Scoring Logic

### Base Score: 500 (Neutral)

### Positive Factors (Score Increases)
1. **Repayment Excellence** (+0-180 points): Strong repay-to-borrow ratio
2. **Activity Diversity** (+0-120 points): High transaction volume and variety
3. **Asset Diversification** (+0-100 points): Multiple asset interactions
4. **Healthy Deposits** (+0-100 points): Good deposit-to-borrow ratio
5. **Long-term Engagement** (+0-80 points): Extended protocol usage
6. **Consistency** (+0-40 points): Stable transaction patterns
7. **Regular User Bonus** (+50 points): Sustained, regular activity

### Negative Factors (Score Decreases)
1. **Liquidation Penalty** (-0-500 points): History of liquidations
2. **Non-Repayment** (-300 points): Borrowed but never repaid
3. **Bot Behavior** (-100 points): Burst activity patterns
4. **Night Activity** (-0-150 points): Excessive off-hours trading
5. **Minimal Activity** (-150 points): Single transaction users
6. **Zero Activity** (-400 points): No meaningful interactions

### Risk Categories
- **Excellent** (900-1000): Highly reliable users
- **Very Low Risk** (700-899): Trustworthy with minor concerns
- **Low Risk** (500-699): Average users with some risk factors
- **Medium Risk** (300-499): Elevated risk requiring attention
- **High Risk** (0-299): Significant concerns or exploitative behavior

## Implementation

### Quick Start
```bash
# Run the complete scoring pipeline
python preprocess.py

# This will:
# 1. Load user-wallet-transactions.json
# 2. Engineer features for each wallet
# 3. Calculate credit scores
# 4. Generate wallet_credit_scores.csv
```

### File Structure
```
├── explore.py              # Main scoring system
├── models.ipynb           # ML model validation
├── plots.ipynb            # Data visualization
├── user-wallet-transactions.json  # Input data
├── wallet_credit_scores.csv       # Output results
├── ml_model_results.csv           # Model performance
└── feature_importance.csv         # Feature rankings
```


### Output Format
The system generates a CSV file with:
- **credit_score**: 0-1000 score for each wallet
- **risk_category**: Risk classification
- **Key metrics**: Transaction counts, ratios, behavioral indicators

## Model Validation Results

### Machine Learning Performance
- **Random Forest**: R² = 0.9858, RMSE = 26.37
- **XGBoost**: R² = 0.9869, RMSE = 25.30  
- **CatBoost**: R² = 0.9890, RMSE = 23.17

### Top Feature Importance
1. **repay_to_borrow_ratio**: Primary creditworthiness indicator
2. **total_transactions**: Activity level importance
3. **deposit_to_borrow_ratio**: Collateral behavior significance
4. **has_repaid**: Binary repayment history
5. **unique_assets**: Diversification impact

## Key Insights

### Score Distribution
- **Median Score**: ~485 (slightly below neutral)
- **Distribution**: Right-skewed with concentration in 400-600 range
- **Risk Categories**: Majority classified as Low to Medium risk

### Behavioral Patterns
- **Repayment Behavior**: Strongest predictor of creditworthiness
- **Activity Consistency**: Regular users score significantly higher
- **Asset Diversity**: Correlates positively with reliability
- **Liquidation Impact**: Severe negative impact on scores

## Extensibility & Customization

### Adjusting Score Weights
Modify the `calculate_credit_scores()` method to adjust factor weights:
```python
# Example: Increase repayment weight
repay_bonus = np.clip(features_df['repay_to_borrow_ratio'] * 150, 0, 200)
```

### Adding New Features
Extend the `engineer_features()` method:
```python
# Example: Add new behavioral metric
features['new_metric'] = wallet_groups['custom_calculation']
```

### Risk Category Customization
Adjust bins in `analyze_scores()` method:
```python
# Example: More granular risk categories
bins=[0, 200, 400, 600, 750, 850, 1000]
```

## Technical Requirements

### Dependencies
```bash
pip install -r requirements.txt
```

### Performance
- **Processing Speed**: ~100K transactions in <30 seconds
- **Memory Usage**: <500MB for typical datasets
- **Scalability**: Linear scaling with transaction volume


## License & Usage

This credit scoring system is designed for research and development purposes. Ensure compliance with relevant regulations when implementing in production environments.

---

**Author**: [Kevin Cherian George](https://github.com/kevin-291)
