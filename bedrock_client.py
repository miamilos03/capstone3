"""
bedrock_client.py -- shared helper for calling Claude via Bedrock.

Every lab and lesson this week that calls Claude reuses this exact module.
This calls Claude via Bedrock, not the direct Anthropic SDK -- students in
this environment don't have direct Anthropic API keys, so the
inference-profile ARN pattern below is the only path to Claude Sonnet 4.6
available here.
"""
from tokenomics_logger import log_token_usage
import boto3
import json

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")


def get_model_id() -> str:
    account_id = boto3.client("sts").get_caller_identity()["Account"]
    return f"arn:aws:bedrock:us-east-1:{account_id}:inference-profile/us.anthropic.claude-sonnet-4-6"


def invoke_claude(
    prompt: str,
    max_tokens: int = 500,
    component: str = "unspecified",
) -> dict:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    model_id = get_model_id()

    response = bedrock.invoke_model(
        modelId=model_id,
        body=json.dumps(body),
    )

    result = json.loads(response["body"].read())

    output = {
        "text": result["content"][0]["text"],
        "input_tokens": result["usage"]["input_tokens"],
        "output_tokens": result["usage"]["output_tokens"],
    }

    log_token_usage(
        component=component,
        model_id=model_id,
        input_tokens=output["input_tokens"],
        output_tokens=output["output_tokens"],
    )

    return output


def invoke_claude_raw(body: dict) -> dict:
    """
    Lower-level helper for calls that need the full Messages API shape --
    system prompts, tool definitions, multi-turn conversations with
    tool_use/tool_result blocks -- that invoke_claude() doesn't cover.
    Returns the parsed response as a plain dict, matching the same shape
    as the Anthropic SDK's response object, accessed with ["..."] instead
    of attribute access.
    """
    body = {**body}
    body.setdefault("anthropic_version", "bedrock-2023-05-31")
    response = bedrock.invoke_model(modelId=get_model_id(), body=json.dumps(body))
    return json.loads(response["body"].read())
