# pylint: disable=unused-argument
import os
import requests

from openai import OpenAI
from fastapi import APIRouter, Request

from utils import query_index, get_num_tokens
from constants import MAX_CONTEXT_LENGTHS, PROMPT

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
router = APIRouter()
GITHUB_AUTH_TOKEN = os.environ["GITHUB_AUTH_TOKEN"]


@router.post("/generate_issue_response", response_model=str)
async def generate_issue_response(request: Request, query: str, model="gpt-4"):
    data = await request.json
    if data["action"] == "opened":
        issue_comment_url = data["issue"]["comments_url"]
        headers = {"Authorization": f"token {GITHUB_AUTH_TOKEN}"}
        comment = {"body": "Thank you for opening an issue. We will look into it ASAP!"}
        requests.post(issue_comment_url, json=comment, headers=headers, timeout=120)

    # Make a call to Pinecone to get the top 20 contexts
    results = query_index(
        query=query,
        k=20,
        filter_dict={},
        alpha=0.9,
        namespace="prod-text-embedding-ada-002",  # TODO change
    )

    token_count = 0
    token_limit = MAX_CONTEXT_LENGTHS[model]
    for context in results:
        text = context["metadata"]["text"]

        # if the length of the context is above the token limit, skip it
        if (
            token_count
            + get_num_tokens(
                "<|im_start|>system" + PROMPT + "<|im_end|>\n" + text + "\n"
            )
        ) > token_limit:
            print("Context too long, skipping...")
            continue
        else:
            context_text += text + "\n"

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "text": PROMPT},
            {"role": "user", "text": context_text},
            {"role": "user", "text": query},
        ]
    )

    return response.choices[0].message.content, 200
