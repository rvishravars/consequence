package com.consequence.service;

import com.consequence.model.EvalCase;
import com.consequence.model.EvalResult;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.assertj.core.api.Assertions.assertThat;

@ExtendWith(MockitoExtension.class)
class EvalServiceScoringTest {

    @Mock
    private AgentService agentService;

    @InjectMocks
    private EvalService evalService;

    // -------------------------------------------------------------------------
    // EXACT scoring
    // -------------------------------------------------------------------------

    @Test
    void exact_pass_whenOutputMatchesCaseInsensitive() {
        EvalCase c = EvalCase.builder()
                .id("c1").scoringMethod(EvalCase.ScoringMethod.EXACT)
                .expectedOutput("Paris").build();

        assertThat(evalService.score(c, "paris")).isEqualTo(EvalResult.Verdict.PASS);
        assertThat(evalService.score(c, "PARIS")).isEqualTo(EvalResult.Verdict.PASS);
        assertThat(evalService.score(c, "  Paris  ")).isEqualTo(EvalResult.Verdict.PASS);
    }

    @Test
    void exact_fail_whenOutputDiffers() {
        EvalCase c = EvalCase.builder()
                .id("c1").scoringMethod(EvalCase.ScoringMethod.EXACT)
                .expectedOutput("Paris").build();

        assertThat(evalService.score(c, "London")).isEqualTo(EvalResult.Verdict.FAIL);
    }

    // -------------------------------------------------------------------------
    // CONTAINS scoring
    // -------------------------------------------------------------------------

    @Test
    void contains_pass_whenOutputContainsExpected() {
        EvalCase c = EvalCase.builder()
                .id("c2").scoringMethod(EvalCase.ScoringMethod.CONTAINS)
                .expectedOutput("hello").build();

        assertThat(evalService.score(c, "Hello, world!")).isEqualTo(EvalResult.Verdict.PASS);
    }

    @Test
    void contains_fail_whenOutputDoesNotContainExpected() {
        EvalCase c = EvalCase.builder()
                .id("c2").scoringMethod(EvalCase.ScoringMethod.CONTAINS)
                .expectedOutput("hello").build();

        assertThat(evalService.score(c, "Goodbye, world!")).isEqualTo(EvalResult.Verdict.FAIL);
    }

    @Test
    void contains_fail_whenExpectedOutputIsNull() {
        EvalCase c = EvalCase.builder()
                .id("c2").scoringMethod(EvalCase.ScoringMethod.CONTAINS)
                .expectedOutput(null).build();

        assertThat(evalService.score(c, "anything")).isEqualTo(EvalResult.Verdict.FAIL);
    }

    // -------------------------------------------------------------------------
    // REGEX scoring
    // -------------------------------------------------------------------------

    @Test
    void regex_pass_whenOutputMatchesPattern() {
        EvalCase c = EvalCase.builder()
                .id("c3").scoringMethod(EvalCase.ScoringMethod.REGEX)
                .expectedPattern("\\d{3}[-.\\s]?\\d{3}[-.\\s]?\\d{4}").build();

        assertThat(evalService.score(c, "Call me at 555-123-4567!")).isEqualTo(EvalResult.Verdict.PASS);
    }

    @Test
    void regex_fail_whenOutputDoesNotMatchPattern() {
        EvalCase c = EvalCase.builder()
                .id("c3").scoringMethod(EvalCase.ScoringMethod.REGEX)
                .expectedPattern("\\d{3}[-.\\s]?\\d{3}[-.\\s]?\\d{4}").build();

        assertThat(evalService.score(c, "No numbers here")).isEqualTo(EvalResult.Verdict.FAIL);
    }

    @Test
    void regex_fail_whenPatternIsNull() {
        EvalCase c = EvalCase.builder()
                .id("c3").scoringMethod(EvalCase.ScoringMethod.REGEX)
                .expectedPattern(null).build();

        assertThat(evalService.score(c, "anything")).isEqualTo(EvalResult.Verdict.FAIL);
    }

    // -------------------------------------------------------------------------
    // NONE scoring
    // -------------------------------------------------------------------------

    @Test
    void none_alwaysPasses() {
        EvalCase c = EvalCase.builder()
                .id("c4").scoringMethod(EvalCase.ScoringMethod.NONE).build();

        assertThat(evalService.score(c, "any output")).isEqualTo(EvalResult.Verdict.PASS);
        assertThat(evalService.score(c, "")).isEqualTo(EvalResult.Verdict.PASS);
        assertThat(evalService.score(c, null)).isEqualTo(EvalResult.Verdict.PASS);
    }

    // -------------------------------------------------------------------------
    // Null actual output
    // -------------------------------------------------------------------------

    @Test
    void anyMethod_failsWhenActualOutputIsNull() {
        for (EvalCase.ScoringMethod method : EvalCase.ScoringMethod.values()) {
            if (method == EvalCase.ScoringMethod.NONE) continue;
            EvalCase c = EvalCase.builder()
                    .id("cx").scoringMethod(method)
                    .expectedOutput("x").expectedPattern("x").build();
            assertThat(evalService.score(c, null))
                    .as("Expected FAIL for null actualOutput with scoring=%s", method)
                    .isEqualTo(EvalResult.Verdict.FAIL);
        }
    }
}
