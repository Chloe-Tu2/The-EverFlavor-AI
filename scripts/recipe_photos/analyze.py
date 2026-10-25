"""Summarize manifest.csv: counts, failures, sizes, shared images."""
import sys

import pandas as pd

m = pd.read_csv(sys.argv[1])
u = m.drop_duplicates("url")
print("rows", len(m), "urls", len(u))
print(u.groupby("source").agg(urls=("url", "size"), ok=("http_status", lambda s: (s == 200).sum()),
                              GB=("bytes", lambda b: b.sum() / 1e9)))
print("fail reasons", u[u.http_status != 200].groupby(["source", "error"]).size().to_dict())
print("formats", u.groupby(["source", "format"]).size().to_dict())
print("image errors", u.image_error.value_counts().to_dict())
ok = u[u.http_status == 200]
print("bytes quantiles", ok.bytes.quantile([0, .01, .5, .99, 1]).to_dict())
print("tiny (<5 KB or <100 px)", ((ok.bytes < 5000) | (ok.width < 100) | (ok.height < 100)).sum())
print("dims top", ok.groupby(["width", "height"]).size().sort_values().tail(5).to_dict())
okr = m[m.http_status == 200]
for key in ("sha256", "ahash"):
    g = okr.groupby(key).agg(recipes=("recipe_id", "nunique"), urls=("url", "nunique"), ex=("url", "first"),
                             names=("recipe_name", lambda s: "; ".join(s.astype(str).unique()[:3])))
    big = g[g.recipes >= 3].sort_values("recipes", ascending=False)
    print(f"{key}: images shared by 3+ recipes: {len(big)} covering {big.recipes.sum()} recipes")
    print(big.head(8).to_string())
same_url = okr.groupby("url").recipe_id.nunique()
print("urls used by 3+ recipes", (same_url >= 3).sum(), "by 2+", (same_url >= 2).sum())
print("hosts", u.url.str.extract(r"https?://([^/]+)")[0].value_counts().to_dict())
