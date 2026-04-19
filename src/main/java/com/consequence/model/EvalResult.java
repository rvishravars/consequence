package com.consequence.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/** The outcome of running a single {@link EvalCase} against an agent. */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class EvalResult {

    private String caseId;
    private String description;
    private String input;
    private String expectedOutput;
    private String actualOutput;
    private Verdict verdict;
    /** Time taken to receive the agent response, in milliseconds. */
    private long latencyMs;
    /** Optional error message when the agent call failed. */
    private String errorMessage;

    public enum Verdict {
        PASS,
        FAIL,
        ERROR
    }

    public boolean isPassed() {
        return Verdict.PASS == verdict;
    }
}
