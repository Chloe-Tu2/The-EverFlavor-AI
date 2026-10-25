"""Build the list of photo links: one row per (source, recipe_id, url)."""
import json, string, sys, time, urllib.request
from pathlib import Path
import pandas as pd
from datasets import load_dataset

REPO = Path(sys.argv[1])
OUT = Path(sys.argv[2])
REV = "33ff70ba3dc1a1a77395fc477934b4ffb18a347d"

proc = pd.concat([pd.read_parquet(REPO / f"data/processed/recipes_{s}.parquet", columns=["recipe_id", "source", "recipe_name"])
                  for s in ("train", "val", "test")])
print(proc.source.value_counts())

hf = load_dataset("datahiveai/recipes-with-nutrition", split="train", revision=REV).to_pandas()
hf["recipe_id"] = "hf_" + hf.index.astype(str)
kept = proc[proc.source == "huggingface"]
chk = kept.merge(hf[["recipe_id", "recipe_name"]], on="recipe_id", suffixes=("", "_raw"))
print("hf kept", len(kept), "matched", len(chk), "name equal", (chk.recipe_name == chk.recipe_name_raw.str.replace(r"\s+", " ", regex=True).str.strip()).mean())
hf_rows = hf[hf.recipe_id.isin(set(kept.recipe_id))][["recipe_id", "recipe_name", "image_url"]].copy()
hf_rows["in_full_data"] = True

demo = pd.concat([pd.read_parquet(REPO / f"data/demo/recipes_{s}.parquet", columns=["recipe_name", "image_url"]) for s in ("train", "val", "test")])
demo = demo.dropna(subset=["image_url"])
url2id = hf.dropna(subset=["image_url"]).groupby("image_url").recipe_id.apply(list)
demo_rows = []
unmatched = 0
for _, r in demo.drop_duplicates().iterrows():
    ids = url2id.get(r.image_url)
    if not ids:
        unmatched += 1
        ids = [None]
    for i in ids:
        demo_rows.append({"recipe_id": i, "recipe_name": r.recipe_name, "image_url": r.image_url})
demo_rows = pd.DataFrame(demo_rows)
print("demo rows with url", len(demo), "unique", demo.image_url.nunique(), "unmatched to hf", unmatched)
demo_rows["in_demo"] = True
hfall = hf_rows.merge(demo_rows, on=["recipe_id", "image_url"], how="outer", suffixes=("", "_d"))
hfall["recipe_name"] = hfall.recipe_name.fillna(hfall.recipe_name_d)
hfall = hfall.drop(columns="recipe_name_d").fillna({"in_full_data": False, "in_demo": False})
hfall["in_demo"] = hfall.recipe_id.isin(set(demo_rows.recipe_id)) | hfall.in_demo
hfall["source"] = "huggingface"

# TheMealDB: the raw table has no thumbnail column, so search again (36 calls, free test key "1")
meals = {}
for c in string.ascii_lowercase + string.digits:
    req = urllib.request.Request(f"https://www.themealdb.com/api/json/v1/1/search.php?f={c}",
                                 headers={"User-Agent": "EverFlavorAI-capstone-photo-index/0.1 (student research)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    for m in data.get("meals") or []:
        meals[m["idMeal"]] = m.get("strMealThumb")
    time.sleep(0.4)
md = proc[proc.source == "themealdb"].copy()
md["idMeal"] = md.recipe_id.str.removeprefix("themealdb_")
md["image_url"] = md.idMeal.map(meals)
print("themealdb kept", len(md), "with thumb", md.image_url.notna().sum(), "api meals", len(meals))
md = md[["recipe_id", "recipe_name", "image_url"]].assign(source="themealdb", in_full_data=True, in_demo=False)

links = pd.concat([hfall, md], ignore_index=True).rename(columns={"image_url": "url"})
print("no url:", links.url.isna().groupby(links.source).sum().to_dict())
links = links.dropna(subset=["url"])
links.to_csv(OUT, index=False)
print(links.groupby("source").agg(rows=("url", "size"), urls=("url", "nunique")))
print(links.groupby("source")[["in_full_data", "in_demo"]].sum())
