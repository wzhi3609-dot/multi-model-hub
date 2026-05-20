from backend.config import MODEL_REGISTRY, TAG_CONFIG


def suggest_model(message: str) -> dict:
    """分析用户消息，返回推荐模型及理由"""
    if not message:
        return {
            "model": "deepseek",
            "model_name": "DeepSeek V3",
            "reason": "默认推荐",
            "matched_tags": ["general"],
        }

    matched_tags = _match_tags(message)

    scores = {}
    for model_key, model_info in MODEL_REGISTRY.items():
        if not model_info["enabled"]:
            continue
        score = sum(1 for tag in model_info["tags"] if tag in matched_tags)
        scores[model_key] = (score, model_info)

    if not scores:
        return {
            "model": "deepseek",
            "model_name": "DeepSeek V3",
            "reason": "无可用模型，回退默认",
            "matched_tags": [],
        }

    best_model_key = max(scores, key=lambda k: scores[k][0])
    best_info = scores[best_model_key][1]

    tag_names = [TAG_CONFIG[t]["name"] for t in matched_tags if t in TAG_CONFIG]
    reason = f"匹配到标签: {', '.join(tag_names)}" if tag_names else "没有匹配到特定标签，使用默认推荐"

    return {
        "model": best_model_key,
        "model_name": best_info["name"],
        "reason": reason,
        "matched_tags": matched_tags,
    }


def _match_tags(message: str) -> list[str]:
    """基于关键词匹配标签"""
    text = message.lower()
    matched = set()

    for tag_key, tag_info in TAG_CONFIG.items():
        if tag_key == "general":
            continue
        for keyword in tag_info["keywords"]:
            if keyword.lower() in text:
                matched.add(tag_key)
                break

    if "chinese" in TAG_CONFIG:
        has_chinese = any("\u4e00" <= c <= "\u9fff" for c in message)
        if has_chinese:
            matched.add("chinese")

    if not matched:
        matched.add("general")

    return list(matched)
