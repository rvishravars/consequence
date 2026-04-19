package com.consequence.service;

import com.consequence.model.AgentRequest;
import com.consequence.model.AgentResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Duration;
import java.util.List;

/**
 * Sends prompts to an OpenAI-compatible chat-completions HTTP endpoint and
 * returns the raw text response.
 */
@Slf4j
@Service
public class AgentService {

    private final WebClient webClient;
    private final String model;
    private final Duration timeout;

    public AgentService(
            @Value("${consequence.agent.base-url:http://localhost:11434/v1}") String baseUrl,
            @Value("${consequence.agent.api-key:}") String apiKey,
            @Value("${consequence.agent.model:llama3}") String model,
            @Value("${consequence.agent.timeout-seconds:60}") int timeoutSeconds) {

        this.model = model;
        this.timeout = Duration.ofSeconds(timeoutSeconds);

        WebClient.Builder builder = WebClient.builder()
                .baseUrl(baseUrl)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE);

        if (apiKey != null && !apiKey.isBlank()) {
            builder.defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer " + apiKey);
        }

        this.webClient = builder.build();
        log.info("AgentService configured: baseUrl={}, model={}, timeout={}s",
                baseUrl, model, timeoutSeconds);
    }

    /**
     * Sends {@code prompt} to the agent and returns its reply text.
     *
     * @param prompt the user message
     * @return the agent's text reply
     * @throws AgentCallException if the HTTP call fails or the response is empty
     */
    public String call(String prompt) {
        AgentRequest request = AgentRequest.builder()
                .model(model)
                .messages(List.of(
                        AgentRequest.Message.builder()
                                .role("user")
                                .content(prompt)
                                .build()))
                .build();

        log.debug("Calling agent with prompt: {}", prompt);

        AgentResponse response = webClient.post()
                .uri("/chat/completions")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(AgentResponse.class)
                .timeout(timeout)
                .block();

        if (response == null || response.firstContent() == null) {
            throw new AgentCallException("Agent returned an empty response");
        }

        String content = response.firstContent();
        log.debug("Agent responded: {}", content);
        return content;
    }

    /** Unchecked exception raised when the agent HTTP call fails. */
    public static class AgentCallException extends RuntimeException {
        public AgentCallException(String message) {
            super(message);
        }

        public AgentCallException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
