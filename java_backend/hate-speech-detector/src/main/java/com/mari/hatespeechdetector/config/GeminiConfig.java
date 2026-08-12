package com.mari.hatespeechdetector.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@ConfigurationProperties(prefix = "gemini")
@Configuration
@Data
public class GeminiConfig {
    String key;
    String model;
    String url;
    int batchSize;
    int maxRetries;

}
