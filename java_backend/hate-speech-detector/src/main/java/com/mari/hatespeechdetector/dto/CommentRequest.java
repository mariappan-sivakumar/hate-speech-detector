package com.mari.hatespeechdetector.dto;

import jakarta.validation.Valid;
import lombok.Data;

import java.util.List;

@Data
public class CommentRequest {
    List<String> comments;
}
