package com.mari.hatespeechdetector.service;


import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.mari.hatespeechdetector.config.GeminiConfig;
import com.mari.hatespeechdetector.dto.ClassificationResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class GeminiService {

    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");

    private final GeminiConfig geminiConfig;
    private final ObjectMapper objectMapper = new ObjectMapper();

    private final OkHttpClient httpClient = new OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build();

    public List<ClassificationResult> classifyComments(List<String> comments) {
        List<String> filtered = comments.stream()
                .filter(c -> c != null && !c.isBlank())
                .toList();

        List<ClassificationResult> allResults = new ArrayList<>();
        int batchSize = geminiConfig.getBatchSize();

        for (int i = 0; i < filtered.size(); i += batchSize) {
            List<String> batch = filtered.subList(i, Math.min(i + batchSize, filtered.size()));
            allResults.addAll(classifyBatch(batch));
        }

        return allResults;
    }

    private List<ClassificationResult> classifyBatch(List<String> batch) {
        String prompt = buildPrompt(batch);

        for (int attempt = 1; attempt <= geminiConfig.getMaxRetries(); attempt++) {
            try {
                String rawResponse = callGeminiApi(prompt);
                return parseResponse(rawResponse);
            } catch (JsonProcessingException e) {
                log.warn("JSON parse failed on attempt {}: {}", attempt, e.getMessage());
                if (attempt == geminiConfig.getMaxRetries()) {
                    log.error("All retries exhausted for batch of size {}", batch.size());
                    return fallbackResults(batch);
                }
                sleep(1000L * attempt);
            } catch (IOException e) {
                log.error("Gemini API call failed on attempt {}: {}", attempt, e.getMessage());
                if (attempt == geminiConfig.getMaxRetries()) {
                    return fallbackResults(batch);
                }
                sleep(1000L * (long) Math.pow(2, attempt - 1));
            }
        }

        return fallbackResults(batch);
    }

    private String callGeminiApi(String prompt) throws IOException {
        String url = String.format("%s/%s:generateContent?key=%s",
                geminiConfig.getUrl(),
                geminiConfig.getModel(),
                geminiConfig.getKey());

        String requestBody = objectMapper.writeValueAsString(
                objectMapper.createObjectNode()
                        .set("contents", objectMapper.createArrayNode()
                                .add(objectMapper.createObjectNode()
                                        .set("parts", objectMapper.createArrayNode()
                                                .add(objectMapper.createObjectNode()
                                                        .put("text", prompt)))))
        );
        log.debug("Sending request to Gemini API with prompt: {}", prompt);
        Request request = new Request.Builder()
                .url(url)
                .post(RequestBody.create(requestBody, JSON))
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            if (response.code() == 429) {
                throw new IOException("Rate limit exceeded (HTTP 429)");
            }
            if (!response.isSuccessful()) {
                throw new IOException("Gemini API error: HTTP " + response.code());
            }
            String responseBody = response.body() != null ? response.body().string() : "";
            JsonNode root = objectMapper.readTree(responseBody);
            return root.at("/candidates/0/content/parts/0/text").asText();
        }
    }

    private List<ClassificationResult> parseResponse(String rawText) throws JsonProcessingException {
        String cleaned = rawText
                .replaceAll("(?s)```json\\s*", "")
                .replaceAll("(?s)```\\s*", "")
                .trim();

        return objectMapper.readValue(
                cleaned,
                objectMapper.getTypeFactory().constructCollectionType(List.class, ClassificationResult.class)
        );
    }

    private List<ClassificationResult> fallbackResults(List<String> batch) {
        return batch.stream()
                .map(comment -> ClassificationResult.builder()
                        .comment(comment)
                        .label("No Hate Speech")
                        .confidence("Low")
                        .reason("Classification failed")
                        .type("None")
                        .build())
                .toList();
    }

    private String buildPrompt(List<String> comments) {
        String commentsJson;
        try {
            log.info("Try to convert comments to JSON string");
            commentsJson = objectMapper.writeValueAsString(comments);
        } catch (JsonProcessingException e) {
            log.error("Failed to convert comments to JSON string: {}", e.getMessage());
            commentsJson = comments.toString();
        }

        return """
                You are a hate speech detection model for YouTube comment moderation.
                Model: gemini-3.1-pro-preview

                For each comment in the list below, classify it as:
                - "Hate Speech"    → abusive language, threats, slurs, discrimination, harassment,
                                     or content targeting identity (race, gender, religion, origin)
                - "No Hate Speech" → general opinion, criticism, praise, or neutral content

                Think step by step for each comment:
                1. Does it target a person/group based on identity?
                2. Does it contain threats, slurs, or calls to violence?
                3. Is the language designed to harass or demean?

                Return ONLY a JSON array — one object per comment — in this exact format:
                [
                  {
                    "comment": "<original comment text>",
                    "label": "Hate Speech" | "No Hate Speech",
                    "confidence": "High" | "Medium" | "Low",
                    "reason": "<one sentence explanation>",
                    "type": "Threat" | "Racial/Ethnic" | "Abusive Language" | "Harassment" | "None"
                  }
                ]

                No preamble. No markdown. No explanation. JSON array only.

                Few-shot examples:
                Input: "People like you should not be allowed to speak publicly. Go back to where you came from."
                Output: { "label": "Hate Speech", "confidence": "High", "reason": "Xenophobic language targeting the creator's origin.", "type": "Racial/Ethnic" }

                Input: "I will find you and make you regret posting this."
                Output: { "label": "Hate Speech", "confidence": "High", "reason": "Direct personal threat against the creator.", "type": "Threat" }

                Input: "Disgusting. Your kind is ruining everything."
                Output: { "label": "Hate Speech", "confidence": "High", "reason": "Dehumanizing language targeting an identity group.", "type": "Abusive Language" }

                Input: "This is the worst video, absolute garbage."
                Output: { "label": "Hate Speech", "confidence": "Medium", "reason": "Extremely hostile language targeting the creator.", "type": "Abusive Language" }

                Input: "This is overwhelming."
                Output: { "label": "No Hate Speech", "confidence": "High", "reason": "Expresses personal emotion with no abusive content.", "type": "None" }

                Input: "Good video but too lengthy."
                Output: { "label": "No Hate Speech", "confidence": "High", "reason": "Constructive feedback with no abusive or hateful content.", "type": "None" }

                Comments to classify:
                """ + commentsJson;
    }

    private void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

}