"""Unit tests for step_definitions_generator module (Gherkin parsing, param inference, skeleton rendering)"""
from agents.step_definitions_generator import (
    GherkinStepExtractor,
    ParameterTypeInferencer,
    StepDefinitionSkeletonGenerator,
)


SIMPLE_FEATURE = """Feature: Authentication

Scenario: Successful login
    Given a user with email "admin@test.com"
    When the user logs in with password "password123"
    Then the login should succeed
    And the session token should be generated
"""

OUTLINE_FEATURE = """Feature: Discounts

Scenario Outline: Age-based discount
    Given a customer aged <age>
    When the discount is calculated for amount <amount>
    Then the discount should be <expected>

    Examples:
      | age | amount | expected |
      | 70  | 100    | 15       |
      | 30  | 100    | 5        |
"""

TABLE_FEATURE = """Feature: Bulk import

Scenario: Import multiple users
    Given the following users exist
      | email            | role  |
      | a@test.com       | admin |
      | b@test.com       | user  |
    Then all users should be imported
"""


class TestGherkinStepExtractor:
    def test_extracts_given_when_then(self):
        steps = GherkinStepExtractor().extract_steps(SIMPLE_FEATURE)
        keywords = [s['keyword'] for s in steps]
        assert keywords == ['Given', 'When', 'Then', 'And']

    def test_and_inherits_preceding_primary_keyword(self):
        steps = GherkinStepExtractor().extract_steps(SIMPLE_FEATURE)
        and_step = steps[-1]
        assert and_step['keyword'] == 'And'
        assert and_step['normalized_keyword'] == 'Then'

    def test_step_text_and_line_numbers_captured(self):
        steps = GherkinStepExtractor().extract_steps(SIMPLE_FEATURE)
        assert steps[0]['text'] == 'a user with email "admin@test.com"'
        assert steps[0]['line_number'] == 4

    def test_examples_rows_backfilled_onto_outline_steps(self):
        steps = GherkinStepExtractor().extract_steps(OUTLINE_FEATURE)
        assert len(steps) == 3
        for step in steps:
            assert len(step['examples_rows']) == 2
        assert steps[0]['examples_rows'][0] == {'age': '70', 'amount': '100', 'expected': '15'}

    def test_datatable_marks_preceding_step_has_table(self):
        steps = GherkinStepExtractor().extract_steps(TABLE_FEATURE)
        given_step = steps[0]
        assert given_step['keyword'] == 'Given'
        assert given_step['has_table'] is True

    def test_step_type_tracking_resets_per_scenario(self):
        multi_scenario = """Feature: F

Scenario: One
    Given step one
    And step one b

Scenario: Two
    When step two
    And step two b
"""
        steps = GherkinStepExtractor().extract_steps(multi_scenario)
        assert steps[1]['normalized_keyword'] == 'Given'
        assert steps[3]['normalized_keyword'] == 'When'

    def test_empty_content_returns_no_steps(self):
        assert GherkinStepExtractor().extract_steps("") == []


class TestParameterTypeInferencer:
    def setup_method(self):
        self.inferencer = ParameterTypeInferencer()

    def test_quoted_string_inferred_as_string(self):
        params = self.inferencer.infer_params('a user with email "admin@test.com"')
        assert len(params) == 1
        assert params[0][1] == 'string'

    def test_bare_int_inferred_as_int(self):
        params = self.inferencer.infer_params('the user is 42 years old')
        assert ('int' in [p[1] for p in params])

    def test_bare_float_inferred_as_float(self):
        params = self.inferencer.infer_params('the amount is 19.99 dollars')
        types = [p[1] for p in params]
        assert 'float' in types

    def test_multiple_params_sorted_by_position(self):
        params = self.inferencer.infer_params('transfer "100" from "A" to "B"')
        names = [p[0] for p in params]
        positions = [p[2] for p in params]
        assert positions == sorted(positions)
        assert len(names) == 3

    def test_outline_placeholder_type_from_all_int_examples(self):
        rows = [{'age': '70'}, {'age': '30'}]
        params = self.inferencer.infer_params('a customer aged <age>', rows)
        assert params[0][1] == 'int'

    def test_outline_placeholder_type_from_mixed_examples_is_word(self):
        rows = [{'flag': 'true'}, {'flag': '"quoted"'}]
        params = self.inferencer.infer_params('flag is <flag>', rows)
        assert params[0][1] == 'word'

    def test_outline_placeholder_with_no_examples_defaults_to_string(self):
        params = self.inferencer.infer_params('value is <thing>', [])
        assert params[0][1] == 'string'

    def test_no_params_in_plain_text(self):
        assert self.inferencer.infer_params('the login should succeed') == []


class TestStepDefinitionSkeletonGenerator:
    def setup_method(self):
        self.generator = StepDefinitionSkeletonGenerator('TestService')

    def test_generates_binding_class(self):
        skeleton = self.generator.generate_skeleton(SIMPLE_FEATURE)
        assert '[Binding]' in skeleton
        assert 'public class StepDefinitions' in skeleton

    def test_generates_using_statements_and_namespace(self):
        skeleton = self.generator.generate_skeleton(SIMPLE_FEATURE)
        assert 'using Reqnroll;' in skeleton
        assert 'using TestService;' in skeleton
        assert 'namespace TestService.Tests' in skeleton

    def test_generates_scenario_context_field_and_constructor(self):
        skeleton = self.generator.generate_skeleton(SIMPLE_FEATURE)
        assert 'private readonly ScenarioContext _context;' in skeleton
        assert 'public StepDefinitions(ScenarioContext context)' in skeleton

    def test_generates_one_method_per_unique_step_with_todo(self):
        skeleton = self.generator.generate_skeleton(SIMPLE_FEATURE)
        assert skeleton.count('// TODO: Implement') == 4
        assert '[Given(' in skeleton
        assert '[When(' in skeleton
        assert '[Then(' in skeleton

    def test_dedupes_identical_steps_across_scenarios(self):
        # Dedup key is (normalized_keyword, raw text), so only a byte-identical
        # step repeated in another scenario collapses to one method.
        duplicated = SIMPLE_FEATURE + """
Scenario: Another login
    Given a user with email "admin@test.com"
    Then the login should succeed
"""
        skeleton = self.generator.generate_skeleton(duplicated)
        assert skeleton.count('GivenAUserWithEmail') == 1
        assert skeleton.count('ThenTheLoginShouldSucceed') == 1

    def test_quoted_values_become_cucumber_string_placeholder(self):
        skeleton = self.generator.generate_skeleton(SIMPLE_FEATURE)
        assert '[Given("a user with email {string}")]' in skeleton

    def test_outline_placeholders_become_typed_cucumber_expression(self):
        skeleton = self.generator.generate_skeleton(OUTLINE_FEATURE)
        assert '{int}' in skeleton

    def test_table_step_gets_table_parameter(self):
        skeleton = self.generator.generate_skeleton(TABLE_FEATURE)
        assert 'Table table' in skeleton

    def test_invalid_cucumber_types_are_not_emitted(self):
        # _build_cucumber_expression sanitizes hallucination-prone types; verify
        # none of them leak into generated skeletons even indirectly.
        skeleton = self.generator.generate_skeleton(SIMPLE_FEATURE)
        for bad_type in ('{bool}', '{boolean}', '{date}', '{datetime}', '{uuid}'):
            assert bad_type not in skeleton
