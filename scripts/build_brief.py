from __future__ import annotations

import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = PROJECT_ROOT / "code"
sys.path.insert(0, str(CODE_DIR))

from nutriai import NutriAIPlanner
from nutriai.personas import REQUIRED_PERSONAS


def para(text: str, style):
    return Paragraph(text, style)


def make_table(data, col_widths=None, font_size=7.8):
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7eee9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17201e")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#c9d4cc")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def load_or_create_report():
    report_path = PROJECT_ROOT / "validation_report.json"
    if report_path.exists():
        return json.loads(report_path.read_text(encoding="utf-8"))

    planner = NutriAIPlanner(project_root=PROJECT_ROOT)
    rows = []
    for persona in REQUIRED_PERSONAS:
        result = planner.generate_plan(persona)
        rows.append(
            {
                "persona": persona.name,
                "generation_time_sec": result.generation_time_sec,
                "diversity_score": result.diversity_score,
                "benchmarks": result.benchmarks,
                "capability_checks": result.capability_checks,
                "daily_warnings": {str(day.day): day.warnings for day in result.days},
            }
        )
    return {"dataset_records": int(len(planner.foods)), "personas": rows}


def build_pdf():
    report = load_or_create_report()
    output = PROJECT_ROOT / "brief.pdf"
    doc = SimpleDocTemplate(
        str(output),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.45 * inch,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BriefTitle", parent=styles["Title"], fontSize=17, leading=20, spaceAfter=8, textColor=colors.HexColor("#173b35")))
    styles.add(ParagraphStyle(name="BriefH2", parent=styles["Heading2"], fontSize=11.5, leading=14, spaceBefore=8, spaceAfter=5, textColor=colors.HexColor("#173b35")))
    styles.add(ParagraphStyle(name="BriefBody", parent=styles["BodyText"], fontSize=8.8, leading=11, spaceAfter=4))
    styles.add(ParagraphStyle(name="BriefSmall", parent=styles["BodyText"], fontSize=7.4, leading=9.2, spaceAfter=2))
    styles.add(ParagraphStyle(name="BriefBullet", parent=styles["BodyText"], fontSize=8.4, leading=10.4, leftIndent=8))

    story = []
    story.append(para("NutriAI - Automated Diet Plan Builder", styles["BriefTitle"]))
    story.append(
        para(
            "NutriAI is a full-stack, offline-runnable Streamlit application that generates a 7-day, 3-meal-a-day plan under the 60-second target while enforcing clinical condition filters, allergens, diet modes, diversity, source provenance, and macro/micronutrient analytics.",
            styles["BriefBody"],
        )
    )
    summary_data = [
        ["Item", "Implementation"],
        ["Runtime", "Streamlit UI + pure-Python planning package; runs with streamlit run code/app.py"],
        ["Offline data", f"{report['dataset_records']:,} meal candidates plus USDA/RDA/clinical source-reference files in data/; 97/97 template ingredients covered"],
        ["Clinical rules", "IBS, GERD, type 2 diabetes, hypertension, allergens, cross-contamination, diet and cultural constraints"],
        ["Outputs", "7-day plan, explain tables, RDA analytics, benchmarks, downloadable CSV, required persona checks"],
    ]
    story.append(make_table(summary_data, [1.3 * inch, 6.0 * inch], font_size=8))
    story.append(Spacer(1, 8))
    story.append(para("Architecture", styles["BriefH2"]))
    arch_data = [
        ["Layer", "Responsibility"],
        ["Data layer", "Loads offline food snapshot, USDA ingredient cache, RDA table, clinical lookup CSVs, and clinical rule JSON. No network/API key required during grading."],
        ["Safety layer", "Applies hard exclusions before ranking: diet compatibility, cultural constraints, exact allergen tags, cross-contamination risks, FODMAP, GERD, GI, and sodium rules."],
        ["Retrieval layer", "Embeds meal text and user profile with deterministic dense hashed vectors; scores candidates by cosine similarity."],
        ["Ranking layer", "Optimizes calorie fit, micronutrient priorities, clinical fit, semantic similarity, and diversity penalties."],
        ["Analytics layer", "Computes per-meal and per-day nutrients; compares against age/sex RDA/AI targets and flags gaps below 80%."],
        ["UI layer", "Streamlit dashboard with profile form, plan table, nutrient views, explanations, benchmarks, persona tests, and CSV export."],
    ]
    story.append(make_table(arch_data, [1.15 * inch, 6.15 * inch], font_size=7.5))
    story.append(Spacer(1, 8))
    story.append(para("Data Sources and Rule References", styles["BriefH2"]))
    citations = [
        "USDA FoodData Central API guide and ingredient cache: https://fdc.nal.usda.gov/api-guide.html",
        "NIH Dietary Reference Intakes for RDA/AI targets: https://www.ncbi.nlm.nih.gov/books/NBK56068/",
        "NHLBI DASH eating plan for sodium cap and potassium/calcium/magnesium/fiber emphasis: https://www.nhlbi.nih.gov/education/dash-eating-plan",
        "Monash Low FODMAP program for IBS/FODMAP filtering concepts: https://www.monashfodmap.com/",
        "University of Sydney Glycemic Index database for GI-band filtering concepts: https://glycemicindex.com/",
    ]
    story.append(ListFlowable([ListItem(para(item, styles["BriefSmall"])) for item in citations], bulletType="bullet"))

    story.append(PageBreak())
    story.append(para("BAX-423 Technique Choices", styles["BriefTitle"]))
    technique_data = [
        ["Technique", "Where used", "Why it fits"],
        ["Bloom filter sketching", "Allergen and cross-contamination pre-screening in nutriai/bloom.py and nutriai/rules.py", "Fast, memory-light membership tests before exact safety checks. This demonstrates sketching while preserving zero-allergen guarantees through exact recheck."],
        ["Dense embeddings", "HashedFeature embeddings in nutriai/embedding.py", "Transforms noisy meal text and user clinical/diet profile into vectors without needing model downloads during demo."],
        ["Recommendation ranking", "Multi-stage scorer in nutriai/planner.py", "Balances calorie target, micronutrient priorities, clinical fit, semantic similarity, and diversity to select 21 unique meals."],
    ]
    story.append(make_table(technique_data, [1.35 * inch, 2.65 * inch, 3.35 * inch], font_size=7.3))
    story.append(Spacer(1, 8))
    story.append(para("Benchmarks", styles["BriefH2"]))
    bench = report["personas"][0]["benchmarks"]
    benchmark_data = [
        ["Metric", "Value"],
        ["Food records scanned", f"{bench.get('total_records', 0):,}"],
        ["Safe records for first persona", f"{bench.get('safe_records', 0):,}"],
        ["Bloom filter bits / hashes", f"{bench.get('bloom_filter_bits')} bits / {bench.get('bloom_filter_hashes')} hashes"],
        ["Embedding dimensions", str(bench.get("embedding_dimensions"))],
        ["Candidate vectors scored", f"{bench.get('candidate_vectors_scored', 0):,}"],
        ["Total generation time", f"{bench.get('total_generation_seconds')} seconds"],
    ]
    story.append(make_table(benchmark_data, [2.2 * inch, 5.0 * inch], font_size=8))
    story.append(Spacer(1, 8))
    story.append(
        para(
            "The implementation intentionally avoids heavyweight infrastructure in the live demo path. The app still demonstrates big-data patterns by scanning a 10,750-row deduplicated offline snapshot, sketching allergen membership, embedding candidate text, and ranking thousands of safe records per profile.",
            styles["BriefBody"],
        )
    )

    story.append(PageBreak())
    story.append(para("Required Persona Results", styles["BriefTitle"]))
    persona_header = ["Persona", "Time", "Diversity", "Clinical", "Allergy", "Diet", "Nutrition", "60 sec"]
    persona_rows = [persona_header]
    for item in report["personas"]:
        checks = {check["capability"]: check["status"] for check in item["capability_checks"]}
        persona_rows.append(
            [
                item["persona"],
                f"{item['generation_time_sec']:.2f}s",
                f"{item['diversity_score']:.1f}",
                checks.get("Clinical Condition Filtering", ""),
                checks.get("Allergy Detection & Exclusion", ""),
                checks.get("Dietary Preference Handling", ""),
                checks.get("Macro & Micronutrient Analysis", ""),
                checks.get("Sub-60-Second Generation", ""),
            ]
        )
    story.append(make_table(persona_rows, [0.9 * inch, 0.65 * inch, 0.7 * inch, 0.8 * inch, 0.75 * inch, 0.75 * inch, 0.85 * inch, 0.65 * inch], font_size=7.2))
    story.append(Spacer(1, 8))
    story.append(para("Persona-Specific Evidence", styles["BriefH2"]))
    evidence_items = [
        "Priya: vegetarian, lactose-free, low-FODMAP plan with no garlic/onion/wheat high-FODMAP meals and no dairy exposure.",
        "Ravi: gluten-free GERD plan that excludes high-acid tomato/citrus/fried/spicy triggers and pork.",
        "Mei: vegan, tree-nut-free, low-glycemic plan using fortified foods and low-GI ranking.",
        "James: pescatarian, soy-free, low-sodium/DASH-oriented plan with potassium, magnesium, and omega-3 priority.",
    ]
    story.append(ListFlowable([ListItem(para(item, styles["BriefBody"])) for item in evidence_items], bulletType="bullet"))
    story.append(Spacer(1, 8))
    story.append(para("Explainability", styles["BriefH2"]))
    story.append(
        para(
            "Every selected meal includes a ranking explanation with calorie fit, nutrient fit, clinical fit, similarity, and diversity factors. The Sources tab reports USDA/source-reference coverage, API matches, FDC-linked meal rows, and unmapped ingredient counts. Every excluded example lists the exact reason, such as allergen detected, cross-contamination risk, high-FODMAP food for IBS, GERD trigger, high-GI food for diabetes, or high-sodium food for hypertension.",
            styles["BriefBody"],
        )
    )

    story.append(PageBreak())
    story.append(para("Limitations and Submission Notes", styles["BriefTitle"]))
    story.append(para("Limitations", styles["BriefH2"]))
    limitations = [
        "The app does not call APIs at runtime. USDA FoodData Central is incorporated through a committed ingredient-reference cache with 97/97 template-ingredient coverage; live/cached FDC API matches and offline source-reference rows are counted separately.",
        "Monash Low FODMAP and Glycemic Index data are represented as curated public-guidance lookup mappings, not licensed bulk database exports.",
        "Allergy and GERD/acidity filtering use internal rule maps matched against meal and USDA ingredient terms because the professor source list does not provide dedicated allergy or GERD bulk datasets.",
        "Rules are conservative class-project approximations and should be reviewed by a clinician or registered dietitian before real-world use.",
        "The hashed embedding model is FAISS-ready in spirit but uses numpy cosine retrieval to avoid native binary install risk during demo.",
        "Meal serving multipliers are used for calorie targeting; production software would use ingredient-level recipe scaling and inventory constraints.",
    ]
    story.append(ListFlowable([ListItem(para(item, styles["BriefBody"])) for item in limitations], bulletType="bullet"))
    story.append(Spacer(1, 8))
    story.append(
        KeepTogether(
            [
                para("Submission Run Commands", styles["BriefH2"]),
                make_table(
                    [
                        ["Task", "Command"],
                        ["Install", "pip install -r code\\requirements.txt"],
                        ["Run app", "streamlit run code\\app.py"],
                        ["Run tests", "python -m unittest discover -s code\\tests -v"],
                    ],
                    [1.3 * inch, 5.9 * inch],
                    font_size=8,
                ),
            ]
        )
    )
    story.append(Spacer(1, 8))
    story.append(para("Educational project only. Not medical advice.", styles["BriefSmall"]))

    doc.build(story)
    print(f"Wrote {output}")


if __name__ == "__main__":
    build_pdf()
