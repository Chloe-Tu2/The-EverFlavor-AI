"""Services that read the Food Graph: suggestions, the waiter's context, cookbook groups and map links.

Everything here comes from the graph's edges (Wikidata via notebook 15, the Food Taxonomy, the cuisine lists, the
map's OpenStreetMap tags). Each suggestion says why it is made and from what; nothing is generated, ranked by a
model or inferred. A dish with no edges gets no suggestions: unknown is acceptable, wrong is not.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from ..stores import COUNTRY_CUISINES
from .entities import Ingredient, Place
from .food_graph import FoodGraph, FoodNode


@dataclass(frozen=True)
class Suggestion:
    """One dish to try, with the reason in words and the edge behind it."""
    node: FoodNode
    reason: str      # "same family: dumpling", "a version of biryani", "also from Sichuan"
    relation: str    # in_family, variant_of, origin, eaten_in, part_of
    evidence: str    # "Wikidata P279", "Food Taxonomy", "Wikipedia cuisine list"


def _dishes(nodes: Iterable[FoodNode], skip: str, everflavor_only: bool = True) -> list[FoodNode]:
    seen: dict[str, FoodNode] = {}
    for n in nodes:
        if n.id != skip and n.node_type in ("dish", "variant") and (n.in_everflavor or not everflavor_only):
            seen.setdefault(n.id, n)
    return sorted(seen.values(), key=lambda n: n.name)


def _known_dishes(graph: FoodGraph, nodes: Iterable[FoodNode], skip: str) -> list[FoodNode]:
    """Our dishes only (not the foods and drinks of a cuisine list); the ones tied to fewest places first (most
    particular to the place: a sandwich is on many lists), then by name."""
    found = [n for n in _dishes(nodes, skip) if n.kind == "dish"]
    return sorted(found, key=lambda n: (len(graph.places_of(n.id.removeprefix("dish:"))), n.name))


class GraphRecommendationService:
    """Dishes to try next, only along the graph's edges, each with its reason."""

    def __init__(self, graph: FoodGraph) -> None:
        self.graph = graph

    # ---------------------------------------------------------------- along families
    def related_dishes(self, dish_id: str, limit: int = 8) -> list[Suggestion]:
        """`FoodGraph.related` with the reason for each dish (its closest group first)."""
        out: dict[str, Suggestion] = {}
        for group, relation, members in self.graph.related_groups(dish_id):
            for n in members:
                if group is None:
                    reason = "a version of this dish"
                elif relation == "in_family":
                    reason = f"same family: {group.name}"
                elif n.id == group.id:
                    reason = "the dish this is a version of"
                else:
                    reason = f"another version of {group.name}"
                out.setdefault(n.id, Suggestion(n, reason, relation, "Wikidata P279"))
        return list(out.values())[:limit]

    def related_variants(self, dish_id: str, everflavor_only: bool = False) -> list[Suggestion]:
        """Its own versions, else the other versions of the dish it is a version of (Sindhi biryani for
        Hyderabadi biryani); ours first, the rest marked by `in_everflavor`."""
        own = self.graph.variants_of(dish_id, everflavor_only)
        if own:
            return [Suggestion(n, "a version of this dish", "variant_of", "Wikidata P279") for n in own]
        out = []
        for parent in self.graph.variant_of(dish_id):
            for n in self.graph.variants_of(parent.id.removeprefix("dish:"), everflavor_only):
                if n.id != f"dish:{dish_id}":
                    out.append(Suggestion(n, f"another version of {parent.name}", "variant_of", "Wikidata P279"))
        return out

    def family_members(self, dish_id: str, everflavor_only: bool = True) -> dict[str, list[FoodNode]]:
        """Each of the dish's families (smallest first) with its other dishes."""
        return {f.name: _dishes(self.graph.child_nodes(f.id, "in_family"), f"dish:{dish_id}", everflavor_only)
                for f in self.graph.families_of(dish_id)}

    # ---------------------------------------------------------------- along places
    def _at(self, place_ids: Iterable[str]) -> list[FoodNode]:
        """Dishes from these places: those whose Wikidata origin is one of them, and those with no origin at all
        whose cuisine list is (a dish with an origin elsewhere is only eaten here, not from here)."""
        found: list[FoodNode] = []
        for pid in place_ids:
            found += self.graph.child_nodes(pid, "origin")
            found += [n for n in self.graph.child_nodes(pid, "eaten_in")
                      if not self.graph.parent_nodes(n.id, "origin")]
        return found

    def _below(self, place_id: str) -> list[str]:
        """The place and every place inside it (the taxonomy's part_of edges)."""
        out, todo = [], [place_id]
        while todo:
            current = todo.pop()
            if current not in out:
                out.append(current)
                todo += [n.id for n in self.graph.child_nodes(current, "part_of")]
        return out

    def cuisine_neighbors(self, dish_id: str, limit: int = 12) -> list[Suggestion]:
        """Dishes on the same cuisine list (the place a Wikipedia cuisine list puts it in)."""
        places = self.graph.parent_nodes(f"dish:{dish_id}", "eaten_in")
        return [Suggestion(n, f"also eaten in {p.name}", "eaten_in", "Wikipedia cuisine list")
                for p in places for n in _known_dishes(self.graph, self.graph.child_nodes(p.id, "eaten_in"),
                                                   f"dish:{dish_id}")][:limit]

    def country_neighbors(self, dish_id: str, limit: int = 12) -> list[Suggestion]:
        """Dishes from the same country, its regions included (other Chinese dishes for mapo tofu)."""
        out: list[Suggestion] = []
        for country in self.graph.countries_of(dish_id):
            for n in _known_dishes(self.graph, self._at(self._below(country.id)), f"dish:{dish_id}"):
                out.append(Suggestion(n, f"also from {country.name}", "part_of", "Food Taxonomy"))
        return out[:limit]

    def region_neighbors(self, dish_id: str, limit: int = 12) -> list[Suggestion]:
        """Dishes from the places next to the dish's own (Hunan and Guangdong for a Sichuan dish; other South Asian
        countries for an Indian one), by the taxonomy's siblings."""
        out: list[Suggestion] = []
        for place in self.graph.places_of(dish_id):
            for sibling in self.graph.siblings(place.id):
                for n in _known_dishes(self.graph, self._at(self._below(sibling.id)), f"dish:{dish_id}"):
                    out.append(Suggestion(n, f"from {sibling.name}, next to {place.name}", "part_of",
                                          "Food Taxonomy"))
        return out[:limit]

    def discovery_candidates(self, dish_id: str, limit: int = 12) -> list[Suggestion]:
        """A mix for discovery: versions, then the family, then the same country, then the places next to it,
        taking turns so each kind shows; each dish once."""
        lists = [self.related_variants(dish_id, everflavor_only=True), self.related_dishes(dish_id, limit),
                 self.country_neighbors(dish_id, limit), self.region_neighbors(dish_id, limit)]
        out: dict[str, Suggestion] = {}
        for i in range(max((len(x) for x in lists), default=0)):
            for x in lists:
                if i < len(x):
                    out.setdefault(x[i].node.id, x[i])
        return list(out.values())[:limit]

    # the names the discovery features (Explore, World Tour, Hidden Gems, Kitchen Adventure) will call
    def discover_variants(self, dish_id: str) -> list[Suggestion]:
        return self.related_variants(dish_id)

    def discover_family_members(self, dish_id: str, limit: int = 12) -> list[Suggestion]:
        return [s for s in self.related_dishes(dish_id, limit * 2) if s.relation == "in_family"][:limit]

    def discover_country_neighbors(self, dish_id: str, limit: int = 12) -> list[Suggestion]:
        return self.country_neighbors(dish_id, limit)

    def discover_region_neighbors(self, dish_id: str, limit: int = 12) -> list[Suggestion]:
        return self.region_neighbors(dish_id, limit)

    def discover_related_dishes(self, dish_id: str, limit: int = 8) -> list[Suggestion]:
        return self.related_dishes(dish_id, limit)

    def dishes_at(self, place_id: str, limit: int = 60) -> dict[str, list[FoodNode]]:
        """Explore: the dishes of a place and the places inside it, grouped by their closest family ("Other" when
        Wikidata gives none), families with the most dishes first."""
        groups = CookbookGrouping(self.graph).by_family(
            [n.id.removeprefix("dish:") for n in _known_dishes(self.graph, self._at(self._below(place_id)), "")][:limit])
        return {name: [self.graph.nodes[f"dish:{d}"] for d in ids] for name, ids in groups.items()}


@dataclass(frozen=True)
class WalterContext:
    """What the waiter may say about a dish's place in the graph: names and sources only."""
    dish: str
    kind_of: tuple[str, ...]
    variants: tuple[str, ...]
    variants_not_in_everflavor: tuple[str, ...]
    related: tuple[str, ...]
    countries: tuple[str, ...]
    places: tuple[str, ...]
    sources: tuple[str, ...] = field(default=("Wikidata (CC0) via notebook 15", "the Food Taxonomy"))

    def lines(self) -> list[str]:
        """Plain sentences from fixed templates; every name in them comes from the graph."""
        out = []
        if self.kind_of:
            out.append(f"{self.dish} is a kind of {_and(self.kind_of)}.")
        if self.variants:
            out.append(f"Versions of {self.dish} include {_and(self.variants)}.")
        if self.related:
            out.append(f"If you enjoy {self.dish}, you may also like {_and(self.related[:3])}.")
        if self.places:
            out.append(f"It is from {_and(self.places)}.")
        return out


def _and(names: Iterable[str]) -> str:
    names = list(names)
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


class WalterContextService:
    """The waiter's graph context for a dish. He reads it; he does not add to it."""

    def __init__(self, graph: FoodGraph) -> None:
        self.graph = graph

    def context(self, dish_id: str) -> WalterContext | None:
        me = self.graph.node(f"dish:{dish_id}")
        if me is None:
            return None
        variants = self.graph.variants_of(dish_id)
        return WalterContext(
            dish=me.name,
            kind_of=tuple(n.name for n in [*self.graph.variant_of(dish_id), *self.graph.families_of(dish_id)][:3]),
            variants=tuple(n.name for n in variants if n.in_everflavor),
            variants_not_in_everflavor=tuple(n.name for n in variants if not n.in_everflavor),
            related=tuple(n.name for n in self.graph.related(dish_id, 6)),
            countries=tuple(n.name for n in self.graph.countries_of(dish_id)),
            places=tuple(n.name for n in self.graph.places_of(dish_id)))


class CookbookGrouping:
    """Group saved dishes for My Cookbook: by their closest family, or by country (no UI yet)."""

    def __init__(self, graph: FoodGraph) -> None:
        self.graph = graph

    def family_of(self, dish_id: str) -> str:
        """The dish's closest family: the dish it is a version of, else its smallest family; "" if none."""
        parents = self.graph.variant_of(dish_id) or self.graph.families_of(dish_id)
        return parents[0].name if parents else ""

    def by_family(self, dish_ids: Iterable[str], other: str = "Other") -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}
        for d in dish_ids:
            groups.setdefault(self.family_of(d) or other, []).append(d)
        return dict(sorted(groups.items(), key=lambda kv: (kv[0] == other, -len(kv[1]), kv[0])))

    def by_country(self, dish_ids: Iterable[str], other: str = "Other") -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}
        for d in dish_ids:
            countries = self.graph.countries_of(d)
            groups.setdefault(countries[0].name if countries else other, []).append(d)
        return dict(sorted(groups.items(), key=lambda kv: (kv[0] == other, -len(kv[1]), kv[0])))


class MapLinks:
    """Graph to map: which places on the map go with a dish, an ingredient or a taxonomy place. A place matches by
    its own OpenStreetMap tags only (cuisine, shop kind); it never says what a shop has on its shelves."""

    def __init__(self, graph: FoodGraph, places: Iterable[Place]) -> None:
        self.graph = graph
        self.places = list(places)

    def _serving(self, countries: Iterable[str]) -> list[Place]:
        tags = {COUNTRY_CUISINES[c] for c in countries if c in COUNTRY_CUISINES}
        return [p for p in self.places if tags & {c.lower() for c in p.cuisines}]

    def places_for_dish(self, dish_id: str) -> list[Place]:
        """Map places whose cuisine tag is the cuisine of the dish's country (Indian places for biryani)."""
        return self._serving(n.name for n in self.graph.countries_of(dish_id))

    def places_for_ingredient(self, ingredient: Ingredient) -> list[Place]:
        """Shops of a kind that usually stock a specialty ingredient (its table's store kinds), those whose cuisine
        tag is one of the ingredient's cuisines first. Kinds of shop, not stock."""
        if ingredient.specialty is None:
            return []
        kinds = set(ingredient.specialty.store_kinds)
        cuisines = {c.lower() for c in ingredient.specialty.cuisines}
        found = [p for p in self.places if p.category in kinds]
        return sorted(found, key=lambda p: not (cuisines & {c.lower() for c in p.cuisines}))

    def related_places(self, place_id: str) -> list[FoodNode]:
        """The taxonomy places next to one (its siblings)."""
        return self.graph.siblings(place_id)

    def regional_food_locations(self, place_id: str) -> list[Place]:
        """Map places serving the cuisine of any country in a taxonomy place (South Asia: Indian, Pakistani...)."""
        service = GraphRecommendationService(self.graph)
        countries = [self.graph.nodes[p].name for p in service._below(place_id)
                     if self.graph.nodes[p].node_type == "country"]
        return self._serving(countries)
