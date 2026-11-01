"""DoD-Code 2 : chaque user story de l'épique E9 (formation Simulation) du PRD d'AGENTS.md est citée par au moins un
test de simulation/tests ; une story ajoutée au PRD sans test fait échouer la suite."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def e9_stories():
    prd = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    section = prd.split("#### E9")[1].split("\n### ")[0]
    return sorted(set(re.findall(r"\*\*(US-\d+) \[N\]", section)))


def cited_stories():
    text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "simulation" / "tests").glob("test_*.py")
                     if path.name != Path(__file__).name)
    return set(re.findall(r"US-\d+", text))


def test_the_prd_lists_the_simulation_stories():
    assert e9_stories()[0] == "US-80" and len(e9_stories()) >= 18


def test_every_simulation_story_of_the_prd_is_cited_by_a_test():
    missing = [story for story in e9_stories() if story not in cited_stories()]

    assert missing == [], f"user stories du PRD sans test : {missing}"


# Un test par critère d'acceptation (« - CA »), dans l'ordre du PRD ; les tests hors de simulation/ sont préfixés.
CRITERIA = {
    "US-80": ["test_the_simulation_opens_only_with_parcours_a", "test_a_parcours_needs_its_seven_modules",
              "test_the_prerequisite_note_is_bilingual_and_never_blocking",
              "test_each_parcours_description_summarises_its_regime"],
    "US-81": ["courses/tests/test_content_files.py::test_the_scanner_reports_every_broken_rule_of_a_sample_tree",
              "test_the_company_file_shows_its_rates_through_parameters", "test_parcours_a_is_ngono_mode_sarl"],
    "US-82": ["test_the_piece_is_shown_in_the_current_language", "test_the_values_of_a_piece_are_escaped",
              "test_a_piece_tag_alone_in_its_paragraph_becomes_the_document",
              "test_a_wide_piece_scrolls_inside_its_frame_on_a_390px_phone", "test_an_invoice_names_its_issuer_fully",
              "test_every_displayed_piece_is_marked_as_a_fictitious_teaching_document"],
    "US-97": ["test_a_procedure_says_where_to_go_what_to_bring_what_you_get_and_on_what_basis",
              "test_a_procedure_is_shown_as_a_checklist_of_documents", "test_a_procedure_source_is_an_official_citation"],
    "US-83": ["test_a_journal_question_that_differs_from_the_book_is_reported",
              "assessments/tests/test_journal_question.py::test_the_quiz_correction_marks_each_line_and_shows_the_expected_entry",
              "test_the_exam_page_shows_the_piece_of_the_prompt_without_the_raw_tag"],
    "US-84": ["test_a_stale_balance_piece_is_reported", "test_the_balance_at_the_start_of_a_month_only_counts_earlier_entries"],
    "US-85": ["test_the_declaration_of_the_15th_is_computed_from_the_month", "test_the_vsd_acronym_is_refused",
              "test_the_quiz_correction_shows_the_filled_return",
              "test_a_declaration_answer_that_differs_from_the_tool_is_reported"],
    "US-86": ["test_a_reconciliation_answer_that_differs_from_the_book_is_reported"],
    "US-87": ["test_set_up_costs_come_with_the_capitalisation_trap_question"],
    "US-88": ["test_the_inventory_module_offers_the_stock_and_depreciation_calculators",
              "test_a_year_end_charge_missing_from_the_book_is_reported"],
    "US-89": ["test_parcours_a_stages_the_six_bridge_items", "test_the_minimum_tax_applies_when_it_exceeds_the_corporate_tax",
              "test_the_tax_return_is_limited_to_its_four_key_tables"],
    "US-90": ["test_an_igs_parcours_uses_numeric_questions_only",
              "test_an_igs_company_file_cites_its_regime_and_its_withholding_rate"],
    "US-91": ["test_the_switch_to_the_actual_regime_happens_on_1_january_2027_only"],
    "US-92": ["test_parcours_d_explains_the_eleven_percent_contrast"],
    "US-93": ["test_an_unbalanced_official_entry_is_reported", "test_a_piece_used_nowhere_is_reported",
              "test_a_journal_question_that_differs_from_the_book_is_reported",
              "test_a_declaration_answer_that_differs_from_the_tool_is_reported",
              "test_the_accounting_result_is_products_minus_charges"],
    "US-94": ["test_the_manifest_sets_the_questions_drawn_per_module_for_the_parcours_exam",
              "test_the_pdf_names_the_formation_and_the_parcours"],
    "US-95": ["test_a_rate_without_its_article_is_refused", "test_cnps_rates_are_never_parameters"],
}


def prd_criteria():
    prd = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    section = prd.split("#### E9")[1].split("#### Traçabilité E9")[0]
    counts, story = {}, None
    for line in section.splitlines():
        match = re.match(r"- \*\*(US-\d+)", line)
        if match:
            story = match.group(1)
            counts.setdefault(story, 0)
        elif line.strip().startswith("- CA") and story:
            counts[story] += 1
    return {story: count for story, count in counts.items() if count}


def test_every_acceptance_criterion_of_the_prd_has_its_test():
    """Chaque critère d'acceptation de E9 est associé à un test ; un critère ajouté sans test fait échouer la suite."""
    mismatched = {story: (count, len(CRITERIA.get(story, []))) for story, count in prd_criteria().items()
                  if count != len(CRITERIA.get(story, []))}

    assert mismatched == {}, f"critères (PRD, table) : {mismatched}"


def test_every_named_criterion_test_exists():
    sources = {path.relative_to(ROOT).as_posix(): path.read_text(encoding="utf-8")
               for path in ROOT.glob("*/tests/test_*.py")}
    simulation = "\n".join(text for name, text in sources.items() if name.startswith("simulation/"))
    missing = []
    for tests in CRITERIA.values():
        for test in tests:
            path, _, name = test.rpartition("::")
            text = sources.get(path, "") if path else simulation
            if f"def {name or test}(" not in text:
                missing.append(test)

    assert missing == []


def test_every_criterion_test_makes_assertions():
    """Chaque test associé à un critère vérifie réellement quelque chose (assert ou pytest.raises), et n'est pas
    marqué pour être ignoré."""
    import ast

    sources = {path.relative_to(ROOT).as_posix(): path.read_text(encoding="utf-8")
               for path in ROOT.glob("*/tests/test_*.py")}
    functions = {}
    for name, text in sources.items():
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                functions.setdefault(node.name, []).append((name, node))
    weak = []
    for tests in CRITERIA.values():
        for test in tests:
            name = test.rpartition("::")[2] or test
            for _, node in functions.get(name, []):
                asserts = [n for n in ast.walk(node) if isinstance(n, ast.Assert)
                           or (isinstance(n, ast.Attribute) and n.attr == "raises")]
                skipped = any("skip" in ast.unparse(d) or "xfail" in ast.unparse(d) for d in node.decorator_list)
                if not asserts or skipped:
                    weak.append(name)

    assert weak == []
