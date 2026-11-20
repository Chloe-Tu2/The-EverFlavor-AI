"""The Food Graph: one graph from World down to a recipe, that discovery, the waiter and the map all read.

Nodes (`FoodNode`), each with an id, a name, a slug, a type and the source it comes from:

    world, zone, region, country, division, state, culinary_region   the Food Taxonomy (food_taxonomy.csv)
    cuisine_style                                                    reserved: no sourced table yet, so none
    dish_family                                                      notebook 15 (Wikidata "subclass of")
    dish                                                             the knowledge notebook (dishes.jsonl), or a
                                                                     family member we do not have yet
    variant                                                          a member of a family that is itself a dish
                                                                     (Sindhi biryani under biryani)
    recipe                                                           a recipe row, added by `add_recipes`

Edges (`FoodEdge`) go from the narrower node to the wider one, and each says why it exists:

    part_of      place -> place      food_taxonomy.csv (its parent and its cross-links)
    in_family    dish -> dish_family Wikidata P279, via notebook 15
    variant_of   dish -> dish        Wikidata P279, via notebook 15 (the family is one of our dishes)
    origin       dish -> place       Wikidata P495 "country of origin" (dishes.jsonl `origin`)
    eaten_in     dish -> place       the Wikipedia cuisine list the dish was found on (dishes.jsonl `country`,
                                     `region`): where it is eaten, not always where it began
    recipe_of    recipe -> dish      the app's own dish match (`KnowledgeGraph.find_dish`)

Nothing is added that a source does not state: a dish whose place is not in the taxonomy simply has no place edge,
and no relationship is ever inferred. `parent_nodes` and `child_nodes` are the two ends of these edges.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ..taxonomy import LEVELS, Taxonomy
from .entities import Dish, Recipe

NODE_TYPES = (*LEVELS, "cuisine_style", "dish_family", "dish", "variant", "recipe")
PLACE_TYPES = frozenset(LEVELS)
RELATIONS = ("part_of", "in_family", "variant_of", "origin", "eaten_in", "recipe_of")
LIST_ARTICLE = re.compile(r"^(lists?|varieties|types|kinds) of ", re.IGNORECASE)   # Wikipedia list pages
MAX_RELATED_GROUP = 40   # a family with more members is a broad class, not "more like this" (see `related`)


def is_wikipedia(url: object) -> bool:
    """An https address whose host is Wikipedia itself (en.wikipedia.org), not one that only mentions it."""
    if not isinstance(url, str):
        return False
    parts = urlparse(url)
    host = (parts.hostname or "").lower()
    return parts.scheme == "https" and (host == "wikipedia.org" or host.endswith(".wikipedia.org"))


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


@dataclass(frozen=True)
class FoodNode:
    id: str            # "place:sichuan", "family:Q1854639", "dish:Q191655", "recipe:<url>"
    name: str
    slug: str
    node_type: str
    description: str = ""
    source: str = ""
    kind: str = ""              # dish_family: family, category or grouping; our dish: "dish" or "food or drink"
    in_everflavor: bool = True  # False: on Wikidata, not in our knowledge notebook yet
    url: str = ""               # its Wikipedia article or recipe page, when the source gives one


@dataclass(frozen=True)
class FoodEdge:
    source: str      # the narrower node (a dish)
    target: str      # the wider node (its family)
    relation: str
    evidence: str    # where the link comes from


@dataclass
class FoodGraph:
    """Nodes by id and edges both ways; built with `build`, then read through the traversal methods."""
    nodes: dict[str, FoodNode] = field(default_factory=dict)
    edges: list[FoodEdge] = field(default_factory=list)
    _up: dict[str, list[FoodEdge]] = field(default_factory=lambda: defaultdict(list), repr=False)
    _down: dict[str, list[FoodEdge]] = field(default_factory=lambda: defaultdict(list), repr=False)

    # ---------------------------------------------------------------- building
    def add_node(self, node: FoodNode) -> FoodNode:
        if node.node_type not in NODE_TYPES:
            raise ValueError(f"unknown node type: {node.node_type}")
        return self.nodes.setdefault(node.id, node)

    def add_edge(self, source: str, target: str, relation: str, evidence: str) -> None:
        if relation not in RELATIONS:
            raise ValueError(f"unknown relation: {relation}")
        if source not in self.nodes or target not in self.nodes or source == target:
            return
        if any(e.target == target and e.relation == relation for e in self._up[source]):
            return
        edge = FoodEdge(source, target, relation, evidence)
        self.edges.append(edge)
        self._up[source].append(edge)
        self._down[target].append(edge)

    def add_taxonomy(self, taxonomy: Taxonomy) -> None:
        for n in taxonomy.nodes.values():
            self.add_node(FoodNode(f"place:{n.slug}", n.name, n.slug, n.level, source="food_taxonomy.csv"))
        for n in taxonomy.nodes.values():
            for parent in (n.parent, *n.also_in):
                if parent:
                    self.add_edge(f"place:{n.slug}", f"place:{parent}", "part_of", "food_taxonomy.csv")

    def add_dishes(self, dishes: Mapping[str, Dish], taxonomy: Taxonomy | None = None) -> None:
        """Our dishes, with their places when the taxonomy has them (origin first, then the cuisine list)."""
        for d in dishes.values():
            link = next((x.url for x in d.learn_more if is_wikipedia(x.url)), "")
            self.add_node(FoodNode(f"dish:{d.dish_id}", d.name, slug(d.name), "dish", d.summary[:280],
                                   "dishes.jsonl", kind=d.kind, url=link))
            if taxonomy is None:
                continue
            for country in d.origin:
                place = taxonomy.node_for(country)
                if place:
                    self.add_edge(f"dish:{d.dish_id}", f"place:{place}", "origin", "Wikidata P495")
            place = taxonomy.node_for(d.country, d.region or None) or taxonomy.node_for(d.country)
            if place:
                self.add_edge(f"dish:{d.dish_id}", f"place:{place}", "eaten_in", "Wikipedia cuisine list")

    def add_families(self, families: Iterable[Mapping[str, Any]], taxonomy: Taxonomy | None = None) -> None:
        """Notebook 15's families: a family that is one of our dishes makes its members variants of that dish;
        any other becomes a dish_family node. Members we do not have yet are kept, marked not in EverFlavor, with
        their Wikidata country of origin (P495) as an `origin` edge when the taxonomy has that country."""
        for f in families:
            root = f"dish:{f['qid']}"
            # only a true family that is one of our dishes has variants; a category or grouping stays a group
            is_dish = root in self.nodes and f.get("kind", "family") == "family"
            if not is_dish:
                self.add_node(FoodNode(f"family:{f['qid']}", str(f["name"]), slug(str(f["name"])), "dish_family",
                                       source="Wikidata P279", kind=str(f.get("kind", "family"))))
            for m in f.get("members", []):
                if LIST_ARTICLE.match(str(m.get("name", ""))):   # "Varieties of biryani" is a list, not a version
                    continue
                member = f"dish:{m['qid']}"
                if member not in self.nodes:
                    self.add_node(FoodNode(member, str(m["name"]), slug(str(m["name"])),
                                           "variant" if is_dish else "dish", source="Wikidata P279",
                                           in_everflavor=False, url=str(m.get("wikipedia", ""))))
                    place = taxonomy.node_for(m["country"]) if taxonomy is not None and m.get("country") else None
                    if place:
                        self.add_edge(member, f"place:{place}", "origin", "Wikidata P495 via notebook 15")
                if is_dish:
                    self.add_edge(member, root, "variant_of", "Wikidata P279")
                else:
                    self.add_edge(member, f"family:{f['qid']}", "in_family", "Wikidata P279")

    def add_recipes(self, recipes: Iterable[Recipe]) -> int:
        """Recipes whose dish is linked (`KnowledgeGraph.link_dish`); returns how many were joined."""
        joined = 0
        for r in recipes:
            if r.dish_id and f"dish:{r.dish_id}" in self.nodes:
                self.add_node(FoodNode(f"recipe:{r.recipe_id}", r.title, slug(r.title), "recipe",
                                       source=r.source, url=r.url))
                self.add_edge(f"recipe:{r.recipe_id}", f"dish:{r.dish_id}", "recipe_of", "the app's dish match")
                joined += 1
        return joined

    @classmethod
    def build(cls, dishes: Mapping[str, Dish], taxonomy: Taxonomy | None = None,
              families: Iterable[Mapping[str, Any]] = ()) -> FoodGraph:
        graph = cls()
        if taxonomy is not None:
            graph.add_taxonomy(taxonomy)
        graph.add_dishes(dishes, taxonomy)
        graph.add_families(families, taxonomy)
        return graph

    # ---------------------------------------------------------------- reading
    def node(self, node_id: str) -> FoodNode | None:
        return self.nodes.get(node_id)

    def parent_nodes(self, node_id: str, relation: str | None = None) -> list[FoodNode]:
        return [self.nodes[e.target] for e in self._up.get(node_id, []) if relation in (None, e.relation)]

    def child_nodes(self, node_id: str, relation: str | None = None) -> list[FoodNode]:
        return [self.nodes[e.source] for e in self._down.get(node_id, []) if relation in (None, e.relation)]

    def children(self, node_id: str) -> list[FoodNode]:
        return self.child_nodes(node_id)

    def ancestors(self, node_id: str, relations: Iterable[str] | None = None) -> list[FoodNode]:
        """Every node above, nearest first, along `relations` only when given (("origin", "eaten_in",
        "part_of") walks a dish's places up to World; ("in_family", "variant_of") its families)."""
        allowed = set(relations) if relations is not None else None
        out: dict[str, FoodNode] = {}
        todo = [node_id]
        while todo:
            for edge in self._up.get(todo.pop(0), []):
                if allowed is not None and edge.relation not in allowed:
                    continue
                parent = self.nodes[edge.target]
                if parent.id not in out and parent.id != node_id:
                    out[parent.id] = parent
                    todo.append(parent.id)
        return list(out.values())

    def siblings(self, node_id: str) -> list[FoodNode]:
        """Nodes of the same type under the same parents (other Chinese provinces for Sichuan)."""
        me = self.nodes[node_id]
        seen: dict[str, FoodNode] = {}
        for parent in self.parent_nodes(node_id):
            for child in self.child_nodes(parent.id):
                if child.id != node_id and child.node_type == me.node_type:
                    seen.setdefault(child.id, child)
        return list(seen.values())

    def families_of(self, dish_id: str, kind: str | None = "family") -> list[FoodNode]:
        """The dish's families (dumpling for jiaozi), smallest first; `kind=None` adds categories and groupings."""
        found = [n for n in self.parent_nodes(f"dish:{dish_id}", "in_family") if kind in (None, n.kind)]
        return sorted(found, key=lambda n: len(self._down.get(n.id, [])))

    def variants_of(self, dish_id: str, everflavor_only: bool = False) -> list[FoodNode]:
        """Its variants on Wikidata (Sindhi and Kolkata biryani for biryani), ours first."""
        found = self.child_nodes(f"dish:{dish_id}", "variant_of")
        found = [n for n in found if n.in_everflavor or not everflavor_only]
        return sorted(found, key=lambda n: (not n.in_everflavor, n.name))

    def variant_of(self, dish_id: str) -> list[FoodNode]:
        """The dish this one is a version of (biryani for Hyderabadi biryani)."""
        return self.parent_nodes(f"dish:{dish_id}", "variant_of")

    def recipes_of(self, dish_id: str) -> list[FoodNode]:
        return self.child_nodes(f"dish:{dish_id}", "recipe_of")

    def places_of(self, dish_id: str) -> list[FoodNode]:
        """Its places: Wikidata's origin first, then the cuisine list it is on."""
        ups = self._up.get(f"dish:{dish_id}", [])
        ordered = [e for e in ups if e.relation == "origin"] + [e for e in ups if e.relation == "eaten_in"]
        return list({e.target: self.nodes[e.target] for e in ordered}.values())

    def countries_of(self, dish_id: str) -> list[FoodNode]:
        """The countries of its places (China for a dish from Sichuan), origin first."""
        out: dict[str, FoodNode] = {}
        for place in self.places_of(dish_id):
            chain = [place, *self.ancestors(place.id, ("part_of",))]
            country = next((n for n in chain if n.node_type == "country"), None)
            if country:
                out.setdefault(country.id, country)
        return list(out.values())

    def related(self, dish_id: str, limit: int = 12, everflavor_only: bool = True,
                max_group: int = MAX_RELATED_GROUP) -> list[FoodNode]:
        """Dishes linked by the graph, closest first: its own variants, then the dish it is a version of with that
        dish's other versions, then the other members of its families, smallest group first. Groups larger than
        `max_group` (all members, ours or not) are too broad to be "like this" ("condiment" puts cardamom next to
        hummus) and are left out here; they still show as the dish's kind. No guessing: a dish with no family
        edge has no related dishes."""
        out: dict[str, FoodNode] = {}
        for _, _, members in self.related_groups(dish_id, everflavor_only, max_group):
            for n in members:
                out.setdefault(n.id, n)
        return list(out.values())[:limit]

    def related_groups(self, dish_id: str, everflavor_only: bool = True,
                       max_group: int = MAX_RELATED_GROUP) -> list[tuple[FoodNode | None, str, list[FoodNode]]]:
        """`related`'s groups in order, each as (the group's node, the relation, its members): (None,
        "variant_of", its variants), (biryani, "variant_of", biryani and its other versions), (dumpling,
        "in_family", the family's other dishes). Lets a caller say why a dish is suggested."""
        me = f"dish:{dish_id}"
        groups: list[tuple[FoodNode | None, str, list[FoodNode]]] = [(None, "variant_of",
                                                                      self.child_nodes(me, "variant_of"))]
        for parent in self.parent_nodes(me, "variant_of"):
            groups.append((parent, "variant_of", [parent, *self.child_nodes(parent.id, "variant_of")]))
        for family in self.families_of(dish_id):
            groups.append((family, "in_family", self.child_nodes(family.id, "in_family")))
        close = sorted((g for g in groups[1:] if len(g[2]) <= max_group), key=lambda g: len(g[2]))
        out = []
        for node, relation, group in [groups[0], *close]:   # its variants, then the smallest group first
            members = [n for n in sorted(group, key=lambda n: (not n.in_everflavor, n.name))
                       if n.id != me and n.node_type in ("dish", "variant") and (n.in_everflavor or not everflavor_only)]
            if members:
                out.append((node, relation, members))
        return out

    def path(self, dish_id: str) -> dict[str, list[FoodNode]]:
        """What a dish page shows, all from edges: dish -> family -> related -> country -> its places."""
        return {"families": self.families_of(dish_id), "variant_of": self.variant_of(dish_id),
                "variants": self.variants_of(dish_id), "related": self.related(dish_id),
                "countries": self.countries_of(dish_id), "places": self.places_of(dish_id)}

    def degree(self, node_id: str) -> int:
        """How many edges touch a node: how well the sources know it (used to put known dishes first)."""
        return len(self._up.get(node_id, [])) + len(self._down.get(node_id, []))

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = defaultdict(int)
        for n in self.nodes.values():
            out[n.node_type] += 1
        for e in self.edges:
            out[f"edge:{e.relation}"] += 1
        return dict(out)


def load_families(path: str | Path) -> list[dict]:
    """Notebook 15's families file; [] when it is missing."""
    path = Path(path)
    if not path.exists():
        return []
    return list(json.loads(path.read_text(encoding="utf-8")).get("families", []))
