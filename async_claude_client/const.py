base_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://claude.ai/chats",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Connection": "keep-alive",
}

OI_Headers = {**base_headers, "Content-Type": "application/json"}

GAC_Headers = {**base_headers}

SM_Headers = {
    **base_headers,
    "Accept": "text/event-stream",
    "Content-Type": "application/json",
    "Origin": "https://claude.ai",
    "DNT": "1",
    "TE": "trailers",
}

UL_Headers = {**base_headers, "Origin": "https://claude.ai", "TE": "trailers"}

DEL_Headers = {
    **base_headers,
    "Content-Type": "application/json",
    "Content-Length": "38",
    "Origin": "https://claude.ai",
    "TE": "trailers",
}

CCH_Headers = {**base_headers, "Content-Type": "application/json"}

CNC_Headers = {
    **base_headers,
    'Content-Type': 'application/json',
    "Origin": "https://claude.ai",
    "DNT": "1",
    "TE": "trailers",
}

RC_Headers = {
    **base_headers,
    "Content-Type": "application/json",
    "Origin": "https://claude.ai",
    "TE": "trailers",
}
