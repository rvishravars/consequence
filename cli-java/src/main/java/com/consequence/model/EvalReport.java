package com.consequence.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.List;

/** Aggregated evaluation report for one run across all {@link EvalCase}s. */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class EvalReport {

    private String suiteFile;
    private Instant runAt;
    private int totalCases;
    private int passed;
    private int failed;
    private int errors;
    private long totalLatencyMs;
    private List<EvalResult> results;

    public double passRate() {
        return totalCases == 0 ? 0.0 : (double) passed / totalCases * 100.0;
    }

    public double averageLatencyMs() {
        return totalCases == 0 ? 0.0 : (double) totalLatencyMs / totalCases;
    }
}
