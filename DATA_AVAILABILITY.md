# Data availability

The inputs are the fixed Yelp2018 and Amazon-book processed interaction splits published alongside [LightGCN](https://doi.org/10.1145/3397271.3401063).

| Dataset | Users | Items | Train interactions | Test interactions | Empty test users retained |
|---|---:|---:|---:|---:|---:|
| Yelp2018 | 31,668 | 38,048 | 1,237,259 | 324,147 | 0 |
| Amazon-book | 52,643 | 91,599 | 2,380,730 | 603,378 | 4 |

Obtain `train.txt` and `test.txt` using the Raw or Download option in the upstream [Yelp2018 directory](https://github.com/kuandeng/LightGCN/tree/master/Data/yelp2018) and [Amazon-book directory](https://github.com/kuandeng/LightGCN/tree/master/Data/amazon-book). Save them under `data/lightgcn_text/yelp2018/` and `data/lightgcn_text/amazon-book/`, respectively. The [preparation command in the README](README.md#data-preparation) checks the four text file sizes and SHA-256 values in `configs/raw_inputs.json` before converting the splits. `configs/inputs.json` records NPZ byte hashes, canonical sparse-content hashes, shapes and counts. If an upstream file changes, the checksum check stops before conversion. The exact original download commit is unverified.

Yelp documents separate [dataset use terms](https://s3-media3.fl.yelpcdn.com/assets/srv0/engineering_pages/bea5c1e92bf3/assets/vendor/yelp-dataset-agreement.pdf). [Amazon Product Data](https://cseweb.ucsd.edu/~jmcauley/datasets/amazon/links.html) is background for the original review corpus. The research uses the LightGCN processed splits, whose preparation from original events and ID mappings was not independently reconstructed. Public availability alone does not establish redistribution rights for these files. This artifact provides preparation code, checksums and aggregates. The interaction text, matrices, ID lists and per-user rankings are obtained or generated separately and are excluded from the review archive.
