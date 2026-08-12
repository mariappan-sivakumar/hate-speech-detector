package com.mari.hatespeechdetector.controller;

import com.mari.hatespeechdetector.dto.ClassificationResponse;
import com.mari.hatespeechdetector.dto.ClassificationResult;
import com.mari.hatespeechdetector.dto.CommentRequest;
import com.mari.hatespeechdetector.service.GeminiService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;
import tools.jackson.databind.node.ObjectNode;

import java.util.List;

@Slf4j
@RestController
@RequestMapping("/api")
public class HateSpeechController {
    private final GeminiService geminiService;

    public HateSpeechController(GeminiService geminiService) {
        this.geminiService = geminiService;
    }

    @GetMapping("/health")
    public JsonNode health() {
        ObjectNode objectNode= new ObjectMapper().createObjectNode();
        objectNode.put("status", "ok");
        return objectNode;
    }

    @PostMapping("/classify")
    public ClassificationResponse classify(@RequestBody CommentRequest commentRequest) {
        log.info("Received request to classify {} comments", commentRequest.getComments().size());
        List<ClassificationResult> results = geminiService.classifyComments(commentRequest.getComments());
        return ClassificationResponse.builder().hateSpeechCount((int) results.stream().filter(result-> result.getLabel().equals("Hate Speech")).count())
                .total(results.size())
                .results(results)
                .build();
    }
}
