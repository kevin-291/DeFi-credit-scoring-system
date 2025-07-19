
import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class AaveCreditScorer:
    """
    Comprehensive credit scoring system for Aave V2 DeFi transactions

    Features engineered:
    - Transaction behavior patterns
    - Repayment history and ratios
    - Asset diversity and concentration
    - Temporal activity patterns
    - Risk indicators and bot detection
    - Financial metrics
    """

    def __init__(self):
        self.features = None
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None

    def load_data(self, json_file_path):

        print(f"Loading data from {json_file_path}...")

        with open(json_file_path, 'r') as f:
            data = json.load(f)

        print(f"Loaded {len(data)} transactions")

        # Convert to DataFrame
        records = []
        for record in data:
            flat_record = {
                'userWallet': record.get('userWallet'),
                'timestamp': record.get('timestamp'),
                'action': record.get('action'),
                'amount': record.get('actionData', {}).get('amount'),
                'assetSymbol': record.get('actionData', {}).get('assetSymbol'),
                'assetPriceUSD': record.get('actionData', {}).get('assetPriceUSD'),
            }
            records.append(flat_record)

        df = pd.DataFrame(records)

        # Convert numeric columns
        df['amount_numeric'] = pd.to_numeric(df['amount'], errors='coerce')
        df['asset_price_usd'] = pd.to_numeric(df['assetPriceUSD'], errors='coerce')
        df['usd_value'] = df['amount_numeric'] * df['asset_price_usd']

        # Add time features
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.dayofweek

        print(f"Data preprocessing complete. Shape: {df.shape}")
        print(f"Unique wallets: {df['userWallet'].nunique()}")

        return df

    def engineer_features(self, df):
        """Engineer comprehensive wallet-level features"""

        print("Engineering wallet features...")

        # Group by wallet for efficient processing
        wallet_groups = df.groupby('userWallet')

        # Initialize features dictionary
        features = {}

        # Basic activity metrics
        features['total_transactions'] = wallet_groups.size()
        features['unique_actions'] = wallet_groups['action'].nunique()
        features['unique_assets'] = wallet_groups['assetSymbol'].nunique()
        features['days_active'] = (wallet_groups['timestamp'].max() - 
                                 wallet_groups['timestamp'].min()) / (24 * 3600)
        features['avg_transactions_per_day'] = (features['total_transactions'] / 
                                               np.maximum(features['days_active'], 1))

        # Financial metrics
        features['total_volume_usd'] = wallet_groups['usd_value'].sum()
        features['avg_transaction_size_usd'] = wallet_groups['usd_value'].mean()
        features['max_transaction_size_usd'] = wallet_groups['usd_value'].max()
        features['std_transaction_size_usd'] = wallet_groups['usd_value'].std()
        features['median_transaction_size_usd'] = wallet_groups['usd_value'].median()

        # Action-specific counts
        action_counts = df.groupby(['userWallet', 'action']).size().unstack(fill_value=0)
        actions = ['deposit', 'borrow', 'repay', 'redeemunderlying', 'liquidationcall']

        for action in actions:
            if action in action_counts.columns:
                features[f'{action}_count'] = action_counts[action]
            else:
                features[f'{action}_count'] = 0

        # Time-based features
        features['most_active_hour'] = wallet_groups['hour'].apply(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 12)
        features['night_activity_ratio'] = wallet_groups.apply(
            lambda x: len(x[(x['hour'] < 6) | (x['hour'] > 22)]) / len(x)
        )
        features['weekend_activity_ratio'] = wallet_groups.apply(
            lambda x: len(x[x['day_of_week'].isin([5, 6])]) / len(x)
        )

        # Convert to DataFrame
        feature_df = pd.DataFrame(features).fillna(0)

        # Calculate derived features
        feature_df['repay_to_borrow_ratio'] = (feature_df['repay_count'] / 
                                             np.maximum(feature_df['borrow_count'], 1))
        feature_df['deposit_to_borrow_ratio'] = (feature_df['deposit_count'] / 
                                               np.maximum(feature_df['borrow_count'], 1))
        feature_df['liquidation_ratio'] = (feature_df['liquidationcall_count'] / 
                                         feature_df['total_transactions'])

        # Behavioral indicators
        feature_df['has_borrowed'] = (feature_df['borrow_count'] > 0).astype(int)
        feature_df['has_repaid'] = (feature_df['repay_count'] > 0).astype(int)
        feature_df['has_been_liquidated'] = (feature_df['liquidationcall_count'] > 0).astype(int)

        # Risk indicators
        feature_df['volume_volatility'] = (feature_df['std_transaction_size_usd'] / 
                                          np.maximum(feature_df['avg_transaction_size_usd'], 1))
        feature_df['size_consistency'] = 1 / (1 + feature_df['volume_volatility'])

        # Activity patterns
        feature_df['burst_activity'] = feature_df['avg_transactions_per_day'] > 10
        feature_df['regular_user'] = ((feature_df['total_transactions'] > 10) & 
                                     (feature_df['days_active'] > 30)).astype(int)

        print(f"Feature engineering complete. Features: {len(feature_df.columns)}")
        print(f"Wallets processed: {len(feature_df)}")

        return feature_df

    def calculate_credit_scores(self, features_df):
        """Calculate credit scores using rule-based approach"""

        print("Calculating credit scores...")

        # Start with neutral score
        scores = pd.Series(500, index=features_df.index)

        # Positive factors (creditworthiness indicators)

        # 1. Excellent repayment behavior (highest weight)
        repay_bonus = np.clip(features_df['repay_to_borrow_ratio'] * 120, 0, 180)
        scores += repay_bonus

        # 2. Diverse and active usage
        activity_bonus = np.clip(np.log1p(features_df['total_transactions']) * 25, 0, 120)
        scores += activity_bonus

        # 3. Asset diversification
        diversity_bonus = np.clip(features_df['unique_assets'] * 20, 0, 100)
        scores += diversity_bonus

        # 4. Healthy deposit behavior
        deposit_bonus = np.clip(features_df['deposit_to_borrow_ratio'] * 15, 0, 100)
        scores += deposit_bonus

        # 5. Long-term engagement
        longevity_bonus = np.clip(np.log1p(features_df['days_active']) * 15, 0, 80)
        scores += longevity_bonus

        # 6. Consistent transaction patterns
        consistency_bonus = features_df['size_consistency'] * 40
        scores += consistency_bonus

        # 7. Regular user bonus
        scores += features_df['regular_user'] * 50

        # Negative factors (risk indicators)

        # 1. Liquidation penalty (major red flag)
        liquidation_penalty = features_df['liquidation_ratio'] * 500
        scores -= liquidation_penalty

        # 2. Never repaid penalty
        never_repaid = ((features_df['has_borrowed'] == 1) & 
                       (features_df['has_repaid'] == 0))
        scores.loc[never_repaid] -= 300

        # 3. Bot-like activity penalty
        scores.loc[features_df['burst_activity']] -= 100

        # 4. Excessive night activity penalty
        night_penalty = np.clip((features_df['night_activity_ratio'] - 0.7) * 200, 0, 150)
        scores -= night_penalty

        # 5. Single transaction penalty
        scores.loc[features_df['total_transactions'] == 1] -= 150

        # 6. Zero activity penalty
        scores.loc[features_df['total_transactions'] == 0] -= 400

        # Cap scores between 0 and 1000
        scores = np.clip(scores, 0, 1000)

        print(f"Credit scores calculated. Range: {scores.min():.0f} - {scores.max():.0f}")

        return scores.round().astype(int)

    def analyze_scores(self, features_df, scores):
        """Analyze and categorize credit scores"""

        print("\nAnalyzing credit scores...")

        # Add scores to features
        features_df['credit_score'] = scores

        # Score statistics
        print(f"Score Statistics:")
        print(f"  Min: {scores.min()}")
        print(f"  Max: {scores.max()}")
        print(f"  Mean: {scores.mean():.2f}")
        print(f"  Median: {scores.median():.2f}")
        print(f"  Std: {scores.std():.2f}")

        # Score distribution
        bins = list(range(0, 1001, 100))
        score_dist = pd.cut(scores, bins=bins, right=False).value_counts().sort_index()

        print(f"\nScore Distribution:")
        for interval, count in score_dist.items():
            percentage = (count / len(scores)) * 100
            print(f"  {interval}: {count} wallets ({percentage:.1f}%)")

        # Risk categories
        features_df['risk_category'] = pd.cut(
            scores, 
            bins=[0, 300, 500, 700, 900, 1000], 
            labels=['High Risk', 'Medium Risk', 'Low Risk', 'Very Low Risk', 'Excellent']
        )

        print(f"\nRisk Categories:")
        risk_dist = features_df['risk_category'].value_counts()
        for category, count in risk_dist.items():
            percentage = (count / len(features_df)) * 100
            print(f"  {category}: {count} wallets ({percentage:.1f}%)")

        return features_df

    def save_results(self, features_df, output_file='output/wallet_credit_scores.csv'):
        """Save results to CSV file"""

        print(f"\nSaving results to {output_file}...")

        # Select key columns for output
        output_columns = [
            'credit_score', 'risk_category', 'total_transactions', 
            'unique_assets', 'days_active', 'repay_to_borrow_ratio',
            'deposit_to_borrow_ratio', 'has_borrowed', 'has_repaid', 
            'has_been_liquidated', 'total_volume_usd', 'liquidation_ratio'
        ]

        output_df = features_df[output_columns].copy()
        output_df.to_csv(output_file)

        print(f"Results saved successfully!")

        return output_df

def main():
    """Main execution function"""

    # Initialize scorer
    scorer = AaveCreditScorer()

    # Load data
    df = scorer.load_data('user-wallet-transactions.json')

    # Engineer features
    features_df = scorer.engineer_features(df)

    # Calculate credit scores
    scores = scorer.calculate_credit_scores(features_df)

    # Analyze results
    final_df = scorer.analyze_scores(features_df, scores)

    # Save results
    output_df = scorer.save_results(final_df)

    print("\nCredit scoring complete!")
    return final_df

if __name__ == "__main__":
    results = main()
