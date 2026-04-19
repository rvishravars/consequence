package com.consequence;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

@SpringBootTest
@TestPropertySource(properties = {
        "spring.shell.interactive.enabled=false",
        "consequence.agent.base-url=http://localhost:9999",
        "consequence.agent.model=test-model"
})
class ConsequenceApplicationTests {

    @Test
    void contextLoads() {
        // Verifies the Spring context starts without errors.
    }
}
