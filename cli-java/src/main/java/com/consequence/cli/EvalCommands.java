package com.consequence.cli;

import com.consequence.model.EvalCase;
import com.consequence.model.EvalReport;
import com.consequence.model.EvalResult;
import com.consequence.service.EvalService;
import lombok.RequiredArgsConstructor;
import org.springframework.shell.standard.ShellComponent;
import org.springframework.shell.standard.ShellMethod;
import org.springframework.shell.standard.ShellOption;

import java.io.IOException;
import java.util.List;

/**
 * Spring Shell commands for the agent evaluation CLI.
 *
 * <pre>
 *   eval run --suite path/to/cases.json
 *   eval list --suite path/to/cases.json
 *   eval report --suite path/to/cases.json
 * </pre>
 */
@ShellComponent
@RequiredArgsConstructor
public class EvalCommands {

    private static final String DEFAULT_SUITE = "sample-eval.json";

    private final EvalService evalService;

    /**
     * Run the evaluation suite and print a summary table.
     *
     * @param suite path to the JSON eval-suite file
     */
    @ShellMethod(key = "eval run", value = "Run all eval cases in a suite file against the configured agent")
    public String run(
            @ShellOption(value = "--suite", defaultValue = DEFAULT_SUITE,
                    help = "Path to the JSON eval-suite file")
            String suite) {

        EvalReport report;
        try {
            report = evalService.run(suite);
        } catch (IOException e) {
            return "ERROR: could not load suite file '" + suite + "': " + e.getMessage();
        }

        return formatReport(report, false);
    }

    /**
     * Print a detailed report including individual case outputs.
     *
     * @param suite path to the JSON eval-suite file (already run)
     */
    @ShellMethod(key = "eval report", value = "Run eval suite and print a detailed per-case report")
    public String report(
            @ShellOption(value = "--suite", defaultValue = DEFAULT_SUITE,
                    help = "Path to the JSON eval-suite file")
            String suite) {

        EvalReport evalReport;
        try {
            evalReport = evalService.run(suite);
        } catch (IOException e) {
            return "ERROR: could not load suite file '" + suite + "': " + e.getMessage();
        }

        return formatReport(evalReport, true);
    }

    /**
     * List the eval cases in a suite file without running them.
     *
     * @param suite path to the JSON eval-suite file
     */
    @ShellMethod(key = "eval list", value = "List all eval cases in a suite file without running them")
    public String list(
            @ShellOption(value = "--suite", defaultValue = DEFAULT_SUITE,
                    help = "Path to the JSON eval-suite file")
            String suite) {

        List<EvalCase> cases;
        try {
            cases = evalService.loadCases(suite);
        } catch (IOException e) {
            return "ERROR: could not load suite file '" + suite + "': " + e.getMessage();
        }

        if (cases.isEmpty()) {
            return "No eval cases found in " + suite;
        }

        StringBuilder sb = new StringBuilder();
        sb.append(String.format("Eval cases in: %s%n", suite));
        sb.append(divider(60)).append(System.lineSeparator());
        sb.append(String.format("%-6s %-20s %-12s %s%n", "ID", "Description", "Scoring", "Input (preview)"));
        sb.append(divider(60)).append(System.lineSeparator());

        for (EvalCase c : cases) {
            String inputPreview = c.getInput() == null ? "" :
                    c.getInput().length() > 30 ? c.getInput().substring(0, 30) + "…" : c.getInput();
            sb.append(String.format("%-6s %-20s %-12s %s%n",
                    c.getId(),
                    truncate(c.getDescription(), 20),
                    c.getScoringMethod(),
                    inputPreview));
        }

        sb.append(divider(60)).append(System.lineSeparator());
        sb.append(String.format("Total: %d case(s)%n", cases.size()));
        return sb.toString();
    }

    // -------------------------------------------------------------------------
    // Formatting helpers
    // -------------------------------------------------------------------------

    private String formatReport(EvalReport report, boolean verbose) {
        StringBuilder sb = new StringBuilder();
        sb.append(System.lineSeparator());
        sb.append("═══ Eval Report ═══════════════════════════════════════").append(System.lineSeparator());
        sb.append(String.format("Suite  : %s%n", report.getSuiteFile()));
        sb.append(String.format("Run at : %s%n", report.getRunAt()));
        sb.append(divider(55)).append(System.lineSeparator());
        sb.append(String.format("Total  : %d   Pass: %d   Fail: %d   Error: %d%n",
                report.getTotalCases(), report.getPassed(), report.getFailed(), report.getErrors()));
        sb.append(String.format("Pass%%  : %.1f%%%n", report.passRate()));
        sb.append(String.format("Avg ms : %.0f ms%n", report.averageLatencyMs()));
        sb.append(divider(55)).append(System.lineSeparator());

        if (verbose) {
            for (EvalResult r : report.getResults()) {
                sb.append(String.format("%n[%s] %s  →  %s (%d ms)%n",
                        r.getCaseId(), r.getDescription(), r.getVerdict(), r.getLatencyMs()));
                sb.append(String.format("  Input    : %s%n", r.getInput()));
                if (r.getExpectedOutput() != null) {
                    sb.append(String.format("  Expected : %s%n", r.getExpectedOutput()));
                }
                if (r.getActualOutput() != null) {
                    sb.append(String.format("  Actual   : %s%n", r.getActualOutput()));
                }
                if (r.getErrorMessage() != null) {
                    sb.append(String.format("  Error    : %s%n", r.getErrorMessage()));
                }
            }
            sb.append(System.lineSeparator()).append(divider(55)).append(System.lineSeparator());
        } else {
            // Compact table
            sb.append(String.format("%-6s %-25s %-8s %s%n", "ID", "Description", "Verdict", "Latency"));
            sb.append(divider(55)).append(System.lineSeparator());
            for (EvalResult r : report.getResults()) {
                sb.append(String.format("%-6s %-25s %-8s %d ms%n",
                        r.getCaseId(),
                        truncate(r.getDescription(), 25),
                        r.getVerdict(),
                        r.getLatencyMs()));
            }
        }

        return sb.toString();
    }

    private static String divider(int length) {
        return "─".repeat(length);
    }

    private static String truncate(String s, int maxLen) {
        if (s == null) return "";
        return s.length() > maxLen ? s.substring(0, maxLen - 1) + "…" : s;
    }
}
