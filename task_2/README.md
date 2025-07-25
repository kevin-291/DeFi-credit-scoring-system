# Wallet Risk Score Pipeline

A comprehensive blockchain analytics tool for assessing wallet risk based on transaction patterns and behavioral indicators. This pipeline analyzes Ethereum wallet activity to generate risk scores between 0-1000, helping identify potentially suspicious or high-risk addresses.

## Overview

This pipeline combines transaction frequency, volume patterns, gas usage, and temporal activity to create a composite risk score for Ethereum wallets. The scoring methodology is inspired by industry-standard AML tools used by crypto exchanges and compliance platforms.

## Architecture

```
Data Collection → Feature Engineering → Normalization → Risk Scoring → Export
     ↓                    ↓                ↓             ↓           ↓
Etherscan API    →    Aggregation    →  MinMax     →  Weighted   →  CSV
(External +           (5 key              Scaling      Composite     Output
 Internal TXs)         features)          [0,1]        Score
```

## Data Collection Method

The pipeline retrieves comprehensive transaction data for each wallet using Etherscan's API:

- **External Transactions**: `action=txlist` - Direct wallet-to-wallet transfers
- **Internal Transactions**: `action=txlistinternal` - Contract-induced transactions
- **Pagination Support**: Up to 10,000 records per API call
- **Output**: Flattened CSV (`wallet_txns_combined.csv`) with columns:
  - `wallet_id`, `action`, `timestamp`, `value`, `gas`, `gasUsed`

## Feature Engineering

### Core Risk Indicators

| Feature | Description | Risk Rationale |
|---------|-------------|----------------|
| **days_active** | Days between first and last transaction | Short-lived wallets may indicate temporary/suspicious usage |
| **n_txs** | Total number of transactions | High frequency could signal automated or abusive patterns |
| **total_value_eth** | Cumulative ETH value moved | Large volumes may indicate money laundering or mixing |
| **total_gas_used** | Sum of gas consumed across all transactions | Complex contract interactions suggest advanced usage patterns |
| **last_tx_days_ago** | Days since most recent transaction | Dormant wallets may be abandoned or intentionally inactive |

### Why These Features?

- **Activity Span**: New wallets with short lifespans often correlate with higher risk
- **Transaction Frequency**: Intensive usage patterns can indicate both legitimate high-activity users and potential abuse
- **Value Movement**: Higher transaction volumes align with traditional AML red flags
- **Gas Consumption**: Reflects interaction complexity and potential sophistication of operations
- **Recency**: Account dormancy can signal abandonment or intentional concealment

## Normalization Strategy

**Method**: MinMax Scaling using `sklearn.preprocessing.MinMaxScaler`

```python
scaler = MinMaxScaler()
normalized_features = scaler.fit_transform(features[['days_active', 'n_txs', 'total_value_eth', 'total_gas_used', 'last_tx_days_ago']])
```

**Benefits**:
- Scales all features to [0,1] range
- Prevents any single metric from dominating the score
- Ensures fair weighting across different measurement scales
- Standard practice in composite scoring models

## Risk Scoring Algorithm

### Composite Score Formula

```python
Risk Score = (
    (1 − days_active_norm) × 0.20 +     # Less activity span = higher risk
    n_txs_norm × 0.20 +                 # More transactions = higher risk  
    total_value_eth_norm × 0.25 +       # Higher volume = higher risk
    total_gas_used_norm × 0.15 +        # More gas usage = higher risk
    last_tx_days_ago_norm × 0.20        # Longer inactivity = higher risk
) × 1000
```

### Weight Distribution

- **Volume (25%)**: Primary risk indicator - high-value movements are strongest AML signal
- **Frequency (20%)**: Transaction patterns reveal usage intensity
- **Recency (20%)**: Account activity status affects risk profile
- **Activity Span (20%)**: Account age and longevity indicate legitimacy
- **Gas Usage (15%)**: Technical complexity and interaction patterns

### Score Interpretation

- **0-200**: Low Risk - Typical retail user patterns
- **201-400**: Low-Medium Risk - Active users with normal patterns
- **401-600**: Medium Risk - Higher activity requiring attention
- **601-800**: High Risk - Suspicious patterns warrant investigation
- **801-1000**: Critical Risk - Immediate review recommended

## 🚀 Getting Started

### Prerequisites

```bash
pip install pandas scikit-learn python-dotenv requests
```

### Environment Setup

Create a `.env` file:
```python
ETHERSCAN_API_KEY=your_api_key_here
```
