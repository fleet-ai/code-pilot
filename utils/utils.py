import tiktoken


def get_num_tokens(text):
    """Get number of tiktoken tokens"""
    encoding = tiktoken.encoding_for_model("text-embedding-ada-002")
    return len(encoding.encode(text, allowed_special={"<|endoftext|>"}))


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx : min(ndx + n, l)]
