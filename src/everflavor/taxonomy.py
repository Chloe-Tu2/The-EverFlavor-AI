"""The Food Taxonomy: one shared tree of where food comes from, used by search, the map, Walter and related dishes.

World -> zone (Asia, Middle East & North Africa...) -> food region (East Asia, Levant...) -> country -> division
(a big country's sector: Southern US) -> state or province (Louisiana, Sichuan) -> culinary region (Pacific
Northwest). Food does not follow borders, so it is a tree with cross-links: a node has one parent and may also
belong elsewhere (`also_in`: Turkey is in Anatolia and in Europe; North Africa is in Middle East & North Africa
and in Africa).

The tree lives in `data/reference/food_taxonomy.csv`, written by hand and recorded as a policy (proposed by Claude
for Team EverGlow's review, 2026-11-16). Country, state and region names are exactly the recipes' `origin_country`
and `origin_region` values, so the tree points straight into the data; nothing in it is inferred from recipes.

    >>> tax = load_taxonomy()
    >>> [n.name for n in tax.path("cn_sichuan")]   # World, Asia, East Asia, China, Sichuan
    >>> tax.mask(recipes, "east_asia")            # recipes from China, Japan, South Korea
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

__all__ = ["LEVELS", "TAXONOMY_FILE", "Node", "Taxonomy", "load_taxonomy"]

TAXONOMY_FILE = Path(__file__).resolve().parents[2] / "data" / "reference" / "food_taxonomy.csv"
LEVELS = ("world", "zone", "region", "country", "division", "state", "culinary_region")
_BELOW_COUNTRY = set(LEVELS[LEVELS.index("country") + 1:])


@dataclass(frozen=True)
class Node:
    slug: str
    name: str
    level: str
    parent: str
    also_in: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()


@dataclass
class Taxonomy:
    """The tree: nodes by slug, each node's children (its own and the cross-linked ones), lookups by name."""
    nodes: dict[str, Node]
    children_of: dict[str, list[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for node in self.nodes.values():
            for parent in (node.parent, *node.also_in):
                if parent:
                    self.children_of.setdefault(parent, []).append(node.slug)

    # ---------------------------------------------------------------- walking the tree
    def children(self, slug: str, level: str | None = None) -> list[Node]:
        """The nodes right under `slug` (cross-linked ones included), in the table's order; only `level` if given."""
        return [self.nodes[c] for c in self.children_of.get(slug, []) if level is None or self.nodes[c].level == level]

    def path(self, slug: str) -> list[Node]:
        """From World down to `slug` along its own parents: the breadcrumb."""
        out = []
        while slug:
            out.append(self.nodes[slug])
            slug = self.nodes[slug].parent
        return out[::-1]

    def subtree(self, slug: str) -> set[str]:
        """`slug` and every node under it, cross-links included (Turkey is under Europe too)."""
        seen, todo = set(), [slug]
        while todo:
            current = todo.pop()
            if current not in seen:
                seen.add(current)
                todo += self.children_of.get(current, [])
        return seen

    def ancestor(self, slug: str, level: str) -> Node | None:
        """The node at `level` on `slug`'s own path (the country of Sichuan is China), or None."""
        return next((n for n in self.path(slug) if n.level == level), None)

    # ---------------------------------------------------------------- the data
    def node_for(self, country: object, region: object = None) -> str | None:
        """The deepest node for a recipe's origin_country and origin_region ("United States", "Louisiana")."""
        wanted = [(str(region), _BELOW_COUNTRY), (str(country), {"country"})] if isinstance(region, str) and region \
            else [(str(country), {"country"})]
        for name, levels in wanted:
            for node in self.nodes.values():
                if node.name == name and node.level in levels:
                    return node.slug
        return None

    def countries_in(self, slug: str) -> set[str]:
        """The origin_country names in `slug`'s subtree (the country itself when `slug` is below one)."""
        node = self.nodes[slug]
        if node.level in _BELOW_COUNTRY:
            country = self.ancestor(slug, "country")
            return {country.name} if country else set()
        return {self.nodes[s].name for s in self.subtree(slug) if self.nodes[s].level == "country"}

    def regions_in(self, slug: str) -> set[str]:
        """The origin_region names in `slug`'s subtree (for a node below a country)."""
        return {self.nodes[s].name for s in self.subtree(slug) if self.nodes[s].level in _BELOW_COUNTRY}

    def mask(self, df: pd.DataFrame, slug: str) -> pd.Series:
        """Recipes in `slug`'s branch: by country for a zone, region or country; by origin_region below that."""
        node = self.nodes[slug]
        if node.level == "world":
            return pd.Series(True, index=df.index)
        if node.level in _BELOW_COUNTRY:
            return df["origin_country"].isin(self.countries_in(slug)) & df["origin_region"].isin(self.regions_in(slug))
        return df["origin_country"].isin(self.countries_in(slug))

    def counts(self, df: pd.DataFrame) -> dict[str, int]:
        """How many recipes each node holds (its whole branch), for the explorer's numbers and its muted options."""
        by_country = df["origin_country"].value_counts()
        pairs = df.dropna(subset=["origin_region"]).groupby(["origin_country", "origin_region"]).size()
        by_region = {(str(c), str(r)): int(v) for c, r, v in zip(pairs.index.get_level_values(0),
                                                                 pairs.index.get_level_values(1), pairs.to_numpy())}
        out = {}
        for slug, node in self.nodes.items():
            if node.level in _BELOW_COUNTRY:
                country = self.ancestor(slug, "country")
                names = self.regions_in(slug)
                out[slug] = int(sum(v for (c, r), v in by_region.items() if country and c == country.name and r in names))
            else:
                out[slug] = int(by_country.reindex(list(self.countries_in(slug))).fillna(0).sum())
        return out

    def related(self, slug: str) -> list[Node]:
        """Nearby branches to try next: the node's siblings under its own parent (other Chinese provinces for
        Sichuan, other East Asian countries for Japan)."""
        node = self.nodes[slug]
        return [n for n in self.children(node.parent) if n.slug != slug] if node.parent else []

    def find(self, text: str) -> list[Node]:
        """Nodes whose name or alias is `text` (lower case): "korean" -> South Korea, "cajun" -> Louisiana."""
        text = text.strip().lower()
        return [n for n in self.nodes.values() if text == n.name.lower() or text in n.aliases]


def _split(value: object) -> tuple[str, ...]:
    return tuple(p.strip() for p in str(value or "").split(";") if p.strip())


def load_taxonomy(path: str | Path = TAXONOMY_FILE) -> Taxonomy:
    """Read and check the tree: unique slugs, parents and cross-links that exist, each level below its parent's.

    Raises:
        ValueError: listing every problem, so a bad edit is caught by the tests.
    """
    table = pd.read_csv(path, dtype=str, keep_default_na=False)
    nodes = {r["slug"]: Node(r["slug"], r["name"], r["level"], r["parent"], _split(r["also_in"]),
                             tuple(a.lower() for a in _split(r["aliases"]))) for r in table.to_dict("records")}
    problems = []
    if len(nodes) != len(table):
        problems.append("duplicate slugs")
    for node in nodes.values():
        if node.level not in LEVELS:
            problems.append(f"{node.slug}: unknown level {node.level}")
            continue
        for parent in (node.parent, *node.also_in):
            if parent and parent not in nodes:
                problems.append(f"{node.slug}: unknown parent {parent}")
            elif parent and LEVELS.index(nodes[parent].level) >= LEVELS.index(node.level):
                problems.append(f"{node.slug}: {node.level} cannot sit under {nodes[parent].level} {parent}")
        if not node.parent and node.level != "world":
            problems.append(f"{node.slug}: needs a parent")
    _check_no_cycles(nodes, problems)
    if problems:
        raise ValueError("; ".join(problems))
    return Taxonomy(nodes)


def _check_no_cycles(nodes: dict[str, Node], problems: list[str]) -> None:
    for slug in nodes:
        seen: set[str] = set()
        current: str = slug
        while current and current in nodes:
            if current in seen:
                problems.append(f"{slug}: its parents loop")
                break
            seen.add(current)
            current = nodes[current].parent

