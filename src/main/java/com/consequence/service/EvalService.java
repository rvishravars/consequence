package com.consequence.service;

import com.consequence.model.EvalCase;
import com.consequence.model.EvalReport;
import com.consequence.model.EvalResult;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

/**
 * Loads an eval suite from a JSON file, runs every {@link EvalCase} against the
 * configured agent, scores each result, and produces an {@link EvalReport}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class EvalService {

    private final AgentService agentService;
    private final ObjectMapper objectMapper;

    /**
     * Loads eval cases from {@code suiteFile}, runs them, and returns a report.
     *
     * @param suiteFile path to a JSON file containing an array of {@link EvalCase}
     * @return aggregated {@link EvalReport}
     */
    public EvalReport run(String suiteFile) throws IOException {
        List<EvalCase> cases = loadCases(suiteFile);
        log.info("Loaded {} eval case(s) from {}", cases.size(), suiteFile);

        List<EvalResult> results = new ArrayList<>();
        for (EvalCase evalCase : cases) {
            results.add(runCase(evalCase));
        }

        return buildReport(suiteFile, results);
    }

    /**
     * Loads eval cases from a JSON file.
     */
    public List<EvalCase> loadCases(String suiteFile) throws IOException {
        return objectMapper.readValue(new File(suiteFile),
                new TypeReference<List<EvalCase>>() {});
    }

    // -------------------------------------------------------------------------
    // Internal helpers
    // -------------------------------------------------------------------------

    private EvalResult runCase(EvalCase evalCase) {
        log.info("Running case [{}]: {}", evalCase.getId(), evalCase.getDescription());

        long start = System.currentTimeMillis();
        try {
            String actualOutput = agentService.call(evalCase.getInput());
            long latencyMs = System.currentTimeMillis() - start;

            EvalResult.Verdict verdict = score(evalCase, actualOutput);
            log.info("Case [{}] -> {} ({}ms)", evalCase.getId(), verdict, latencyMs);

            return EvalResult.builder()
                    .caseId(evalCase.getId())
                    .description(evalCase.getDescription())
                    .input(evalCase.getInput())
                    .expectedOutput(evalCase.getExpectedOutput())
                    .actualOutput(actualOutput)
                    .verdict(verdict)
                    .latencyMs(latencyMs)
                    .build();

        } catch (AgentService.AgentCallException e) {
            long latencyMs = System.currentTimeMillis() - start;
            log.warn("Case [{}] -> ERROR: {}", evalCase.getId(), e.getMessage());

            return EvalResult.builder()
                    .caseId(evalCase.getId())
                    .description(evalCase.getDescription())
                    .input(evalCase.getInput())
                    .expectedOutput(evalCase.getExpectedOutput())
                    .actualOutput(null)
                    .verdict(EvalResult.Verdict.ERROR)
                    .latencyMs(latencyMs)
                    .errorMessage(e.getMessage())
                    .build();
        }
    }

    EvalResult.Verdict score(EvalCase evalCase, String actualOutput) {
        if (evalCase.getScoringMethod() == EvalCase.ScoringMethod.NONE) {
            return EvalResult.Verdict.PASS;
        }
        if (actualOutput == null) {
            return EvalResult.Verdict.FAIL;
        }
        return switch (evalCase.getScoringMethod()) {
            case EXACT -> actualOutput.trim().equalsIgnoreCase(
                    evalCase.getExpectedOutput() == null ? "" : evalCase.getExpectedOutput().trim())
                    ? EvalResult.Verdict.PASS : EvalResult.Verdict.FAIL;

            case CONTAINS -> evalCase.getExpectedOutput() != null
                    && actualOutput.toLowerCase().contains(
                            evalCase.getExpectedOutput().toLowerCase())
                    ? EvalResult.Verdict.PASS : EvalResult.Verdict.FAIL;

            case REGEX -> evalCase.getExpectedPattern() != null
                    && Pattern.compile(evalCase.getExpectedPattern(),
                            Pattern.DOTALL | Pattern.CASE_INSENSITIVE)
                            .matcher(actualOutput).find()
                    ? EvalResult.Verdict.PASS : EvalResult.Verdict.FAIL;

            case NONE -> EvalResult.Verdict.PASS;
        };
    }

    private EvalReport buildReport(String suiteFile, List<EvalResult> results) {
        int passed = (int) results.stream().filter(EvalResult::isPassed).count();
        int errors = (int) results.stream()
                .filter(r -> r.getVerdict() == EvalResult.Verdict.ERROR).count();
        long totalLatency = results.stream().mapToLong(EvalResult::getLatencyMs).sum();

        return EvalReport.builder()
                .suiteFile(suiteFile)
                .runAt(Instant.now())
                .totalCases(results.size())
                .passed(passed)
                .failed(results.size() - passed - errors)
                .errors(errors)
                .totalLatencyMs(totalLatency)
                .results(results)
                .build();
    }
}
