package com.consequence.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * A single evaluation case: an input prompt sent to the agent together with
 * criteria used to judge the response.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class EvalCase {

    /** Unique identifier for this case. */
    private String id;

    /** Short human-readable description of what is being tested. */
    private String description;

    /** The prompt (user message) to send to the agent. */
    private String input;

    /**
     * Expected output used for {@code EXACT} and {@code CONTAINS} scoring.
     * May be {@code null} when {@code scoringMethod} is {@code REGEX} or {@code NONE}.
     */
    private String expectedOutput;

    /**
     * Regular expression used when {@code scoringMethod} is {@code REGEX}.
     * May be {@code null} otherwise.
     */
    private String expectedPattern;

    /**
     * How the agent response is scored.
     * Defaults to {@code CONTAINS} when not specified.
     */
    @Builder.Default
    private ScoringMethod scoringMethod = ScoringMethod.CONTAINS;

    public enum ScoringMethod {
        /** Response must equal {@code expectedOutput} (case-insensitive, trimmed). */
        EXACT,
        /** Response must contain {@code expectedOutput} (case-insensitive). */
        CONTAINS,
        /** Response must match {@code expectedPattern} (regular expression). */
        REGEX,
        /** No automatic scoring; result is always marked {@code PASS}. */
        NONE
    }
}
