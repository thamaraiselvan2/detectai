# Real ML Dataset

DetectAI uses the curated Cresci-2017-derived subset at
`data/cresci17_subset/`. The loader assigns labels strictly from source-file
identity:

- `genuine_users.csv` -> label `0`
- `spam_user.csv` -> label `1`

The ML loader never reads SQLite `check_history`, risk levels, detector output,
or rule-engine decisions as labels.

The two source files contain no label column. Their schemas are intentionally
handled separately and are not renamed or copied.

## CSV Contract

For a generic single-file dataset, the loader also supports one profile per row
with these required columns:

```text
label,username,display_name,bio,followers_count,following_count,posts_count,account_age_days,avatar_url,is_verified
```

Optional columns:

```text
ip_signal,device_signal
```

`label` is the target and must be one of:

- `0`, `genuine`, or `real` for a genuine account
- `1`, `fake`, or `suspicious` for a fake/bot account

Numeric columns must contain integer values. Boolean `is_verified` accepts
`0/1`, `true/false`, or `yes/no`. Empty text fields are treated as empty text;
empty numeric fields become zero, and an empty account age becomes one day so
the logarithm is defined. These are explicit compatibility defaults, not labels
or fabricated observations. IP/device signals are optional and default to
`0.0` when the dataset has no security telemetry; this means unavailable, not
known-safe.

The dataset must contain both labels, at least two samples per class, and at
least ten total rows before training is allowed. A stratified 80/20 held-out
split is used for training and evaluation.

## Cresci Column Mapping

The supplied files map these real columns into the canonical DetectAI profile:

| DetectAI field | Cresci column |
| --- | --- |
| `username` | `screen_name` |
| `display_name` | `name` |
| `bio` | `description` |
| `followers_count` | `followers_count` |
| `following_count` | `friends_count` |
| `posts_count` | `statuses_count` |
| `account_age_days` | `timestamp - created_at` in days |
| `avatar_url` | `profile_image_url_https` |
| `is_verified` | `verified` |

The supplied data has no IP or device fields, so `ip_signal` and
`device_signal` are unavailable and remain `0.0` for this offline dataset.
Protected-profile comparison features are also unavailable because this
dataset does not contain a protected identity reference set. They remain
explicitly `0.0`; no comparison labels or values are fabricated.

## Feature Availability

| Feature | CSV source | Availability without protected-profile data |
| --- | --- | --- |
| `username_similarity_max` | username plus a protected baseline | Unavailable; `0.0` |
| `username_levenshtein_min` | username plus a protected baseline | Unavailable; `0.0` |
| `name_similarity_max` | display name plus a protected baseline | Unavailable; `0.0` |
| `bio_similarity_max` | bio plus a protected baseline | Unavailable; `0.0` |
| `follower_following_ratio` | followers/following counts | Supported |
| `account_age_days_norm` | account age | Supported |
| `post_count_norm` | post count | Supported |
| `posting_rate` | posts and account age | Supported |
| `avatar_present` | avatar URL/reference | Supported |
| `avatar_similarity_max` | avatar URL plus a protected baseline | Unavailable; `0.0` |
| `has_phishing_keywords` | bio | Supported |
| `has_suspicious_username` | username | Supported |
| `has_suspicious_affix` | username | Supported |
| `username_entropy` | username | Supported |
| `follower_count_log` | followers count | Supported |
| `following_count_log` | following count | Supported |
| `is_verified` | verified flag | Supported |
| `bio_empty` | bio | Supported |
| `ip_signal` | optional security telemetry | Optional; `0.0` if unavailable |
| `device_signal` | optional security telemetry | Optional; `0.0` if unavailable |

The five protected-baseline comparison features are not fabricated from the
CSV. They become populated only when a caller supplies protected profile data
to `extract_features()` directly. The CSV training path intentionally has no
database dependency.

## Commands

From `backend`, use either an explicit path:

```powershell
python ml/train.py --dataset C:\path\to\profiles.csv
python ml/evaluate.py --dataset C:\path\to\profiles.csv
```

or configuration:

```powershell
python ml/train.py --dataset ..\data\cresci17_subset
python ml/evaluate.py --dataset ..\data\cresci17_subset
```

The same path can be configured through the environment:

```powershell
$env:DETECTAI_ML_DATASET = "..\data\cresci17_subset"
python ml/train.py
python ml/evaluate.py
```

Training fits Logistic Regression as a baseline and Random Forest as the
persisted main model at `model_store/model.pkl`. Evaluation writes measured
precision, recall, F1, ROC-AUC, and confusion-matrix values only after actual
held-out predictions are available. No metrics are generated without a valid
labeled dataset.
