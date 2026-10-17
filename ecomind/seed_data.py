"""SYNTHETIC illustrative data: a fictional school ("Greenfield School").
Nothing here is a real measurement. Replace with a real waste audit before drawing conclusions.
Weights/effects/costs are 0-1 illustrative numbers chosen by the author."""

SYNTHETIC_NOTICE = ("All numbers are synthetic illustrative assumptions for a fictional school, "
                    "not real-world measurements.")

PROBLEMS = [dict(id="school_waste", name="Excess waste at Greenfield School",
                 keywords=["waste", "trash", "garbage", "recycling", "rubbish", "school"])]

CAUSES = [
    dict(id="single_use_plastics", name="Single-use plastic bottles & wrappers"),
    dict(id="food_waste_cafeteria", name="Uneaten cafeteria food"),
    dict(id="paper_overuse", name="Paper overuse"),
    dict(id="poor_sorting", name="Poor waste sorting (contaminated recycling)"),
    dict(id="no_recycling_bins", name="Too few labelled recycling bins"),
    dict(id="low_awareness", name="Low student awareness"),
    dict(id="oversized_portions", name="Fixed oversized portions"),
]

# (Cause)-[:CONTRIBUTES_TO {weight}]->(Problem)
CONTRIBUTES_TO = [
    ("single_use_plastics", "school_waste", 0.25), ("food_waste_cafeteria", "school_waste", 0.35),
    ("paper_overuse", "school_waste", 0.15), ("poor_sorting", "school_waste", 0.25),
]
# (Cause)-[:DRIVES {weight}]->(Cause)
DRIVES = [
    ("no_recycling_bins", "poor_sorting", 0.6), ("low_awareness", "poor_sorting", 0.5),
    ("low_awareness", "food_waste_cafeteria", 0.3), ("oversized_portions", "food_waste_cafeteria", 0.5),
]
INTERVENTIONS = [
    dict(id="compost_program", name="Cafeteria composting program", cost=0.5, effort=0.6,
         description="Collect food scraps for composting."),
    dict(id="portion_options", name="Small/large portion options", cost=0.1, effort=0.2,
         description="Let students choose portion size."),
    dict(id="sorting_stations", name="Labelled sorting stations", cost=0.4, effort=0.3,
         description="Add clearly labelled bins in corridors and the cafeteria."),
    dict(id="awareness_campaign", name="Student awareness campaign", cost=0.1, effort=0.4,
         description="Student-led posters, assemblies and a waste challenge."),
    dict(id="refill_stations", name="Reusable bottle + refill stations", cost=0.3, effort=0.3,
         description="Water refill points and a reusable-bottle drive."),
    dict(id="double_sided_printing", name="Default double-sided printing", cost=0.05, effort=0.1,
         description="Change printer defaults and set class print limits."),
]
# (Intervention)-[:ADDRESSES {effect}]->(Cause)
ADDRESSES = [
    ("compost_program", "food_waste_cafeteria", 0.6), ("portion_options", "oversized_portions", 0.7),
    ("sorting_stations", "no_recycling_bins", 0.8), ("sorting_stations", "poor_sorting", 0.3),
    ("awareness_campaign", "low_awareness", 0.5), ("refill_stations", "single_use_plastics", 0.6),
    ("double_sided_printing", "paper_overuse", 0.5),
]
# Evidence nodes. confidence = author's synthetic confidence in the assumption (0-1).
EVIDENCE = [
    dict(id="ev_compost", label="Synthetic assumption: composting diverts most scraps once bins are used", confidence=0.6),
    dict(id="ev_portion", label="Synthetic assumption: portion choice reduces plate waste", confidence=0.7),
    dict(id="ev_sorting", label="Synthetic assumption: labelled bins reduce contamination", confidence=0.7),
    dict(id="ev_refill", label="Synthetic assumption: refill points reduce bottle use", confidence=0.6),
    dict(id="ev_print", label="Synthetic assumption: duplex defaults cut paper use", confidence=0.8),
    # Note: awareness_campaign intentionally has NO evidence -> engine must flag missing evidence.
]
SUPPORTED_BY = [
    ("compost_program", "ev_compost"), ("portion_options", "ev_portion"),
    ("sorting_stations", "ev_sorting"), ("refill_stations", "ev_refill"),
    ("double_sided_printing", "ev_print"),
]


def seed_statements():
    """Return [(cypher, params)] — parameterised, idempotent (MERGE)."""
    s = []
    s.append(("UNWIND $rows AS r MERGE (n:Problem {id:r.id}) SET n.name=r.name, n.keywords=r.keywords, n.synthetic=true", {"rows": PROBLEMS}))
    s.append(("UNWIND $rows AS r MERGE (n:Cause {id:r.id}) SET n.name=r.name, n.synthetic=true", {"rows": CAUSES}))
    s.append(("UNWIND $rows AS r MERGE (n:Intervention {id:r.id}) SET n.name=r.name, n.cost=r.cost, n.effort=r.effort, n.description=r.description, n.synthetic=true", {"rows": INTERVENTIONS}))
    s.append(("UNWIND $rows AS r MERGE (n:Evidence {id:r.id}) SET n.label=r.label, n.confidence=r.confidence, n.synthetic=true", {"rows": EVIDENCE}))
    def rel(rows, la, lb, typ, prop):
        data = [dict(a=a, b=b, v=v) for (a, b, v) in rows]
        set_clause = f" SET e.{prop}=r.v" if prop else ""
        return (f"UNWIND $rows AS r MATCH (a:{la} {{id:r.a}}), (b:{lb} {{id:r.b}}) MERGE (a)-[e:{typ}]->(b){set_clause}", {"rows": data})
    s.append(rel(CONTRIBUTES_TO, "Cause", "Problem", "CONTRIBUTES_TO", "weight"))
    s.append(rel(DRIVES, "Cause", "Cause", "DRIVES", "weight"))
    s.append(rel(ADDRESSES, "Intervention", "Cause", "ADDRESSES", "effect"))
    s.append(rel([(a, b, None) for a, b in SUPPORTED_BY], "Intervention", "Evidence", "SUPPORTED_BY", None))
    return s
