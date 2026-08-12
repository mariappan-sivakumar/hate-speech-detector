package com.mari.hatespeechdetector.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Data;

import java.util.List;
@Builder
@Data
public class ClassificationResponse {
    int total;
    @JsonProperty("hate_speech_count")
    int hateSpeechCount;
    List<ClassificationResult> results;
}
