package com.consequence.service;

import com.consequence.model.EvalCase;
import com.consequence.model.EvalReport;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.api.io.TempDir;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.io.File;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class EvalServiceRunTest {

    @Mock
    private AgentService agentService;

    private EvalService evalService;

    @BeforeEach
    void setUp() {
        ObjectMapper mapper = new ObjectMapper().registerModule(new JavaTimeModule());
        evalService = new EvalService(agentService, mapper);
    }

    @Test
    void run_producesCorrectPassCount(@TempDir Path tempDir) throws IOException {
        // Write a minimal suite to a temp file
        List<EvalCase> cases = List.of(
                EvalCase.builder().id("1").description("pass case")
                        .input("say hi").expectedOutput("hi")
                        .scoringMethod(EvalCase.ScoringMethod.CONTAINS).build(),
                EvalCase.builder().id("2").description("fail case")
                        .input("say bye").expectedOutput("bye")
                        .scoringMethod(EvalCase.ScoringMethod.CONTAINS).build()
        );

        ObjectMapper mapper = new ObjectMapper().registerModule(new JavaTimeModule());
        File suiteFile = tempDir.resolve("suite.json").toFile();
        mapper.writeValue(suiteFile, cases);

        when(agentService.call("say hi")).thenReturn("hi there!");
        when(agentService.call("say bye")).thenReturn("totally unrelated");

        EvalReport report = evalService.run(suiteFile.getAbsolutePath());

        assertThat(report.getTotalCases()).isEqualTo(2);
        assertThat(report.getPassed()).isEqualTo(1);
        assertThat(report.getFailed()).isEqualTo(1);
        assertThat(report.getErrors()).isEqualTo(0);
    }

    @Test
    void run_countsAgentErrorsCorrectly(@TempDir Path tempDir) throws IOException {
        List<EvalCase> cases = List.of(
                EvalCase.builder().id("1").description("error case")
                        .input("crash").expectedOutput("ok")
                        .scoringMethod(EvalCase.ScoringMethod.CONTAINS).build()
        );

        ObjectMapper mapper = new ObjectMapper().registerModule(new JavaTimeModule());
        File suiteFile = tempDir.resolve("suite.json").toFile();
        mapper.writeValue(suiteFile, cases);

        when(agentService.call("crash"))
                .thenThrow(new AgentService.AgentCallException("timeout"));

        EvalReport report = evalService.run(suiteFile.getAbsolutePath());

        assertThat(report.getErrors()).isEqualTo(1);
        assertThat(report.getPassed()).isEqualTo(0);
    }

    @Test
    void loadCases_returnsAllCases(@TempDir Path tempDir) throws IOException {
        List<EvalCase> cases = List.of(
                EvalCase.builder().id("a").description("a").input("a")
                        .scoringMethod(EvalCase.ScoringMethod.NONE).build(),
                EvalCase.builder().id("b").description("b").input("b")
                        .scoringMethod(EvalCase.ScoringMethod.NONE).build()
        );

        ObjectMapper mapper = new ObjectMapper().registerModule(new JavaTimeModule());
        File suiteFile = tempDir.resolve("suite.json").toFile();
        mapper.writeValue(suiteFile, cases);

        List<EvalCase> loaded = evalService.loadCases(suiteFile.getAbsolutePath());
        assertThat(loaded).hasSize(2);
        assertThat(loaded.get(0).getId()).isEqualTo("a");
    }
}
