import time

import litellm

from litellm import (
    completion,
    Cache,
)

from app.config import settings

from app.services.failure_simulator import (
    get_simulated_failure,
)


# ============================================================
# LITELLM CACHE
# ============================================================

# LiteLLM built-in local/in-memory cache.
litellm.cache = Cache(
    type="local"
)


# ============================================================
# RETRYABLE PROVIDER ERRORS
# ============================================================

RETRYABLE_STATUS_CODES = {
    429,
    500,
    502,
    503,
}


# ============================================================
# STATUS CODE EXTRACTION
# ============================================================

def get_status_code(exception):

    status_code = getattr(
        exception,
        "status_code",
        None,
    )

    if status_code is not None:
        return status_code


    response = getattr(
        exception,
        "response",
        None,
    )

    if response is not None:

        return getattr(
            response,
            "status_code",
            None,
        )


    return None


# ============================================================
# CHECK WHETHER PROVIDER ERROR SHOULD FAIL OVER
# ============================================================

def is_retryable_error(exception):

    status_code = get_status_code(
        exception
    )


    if status_code in RETRYABLE_STATUS_CODES:
        return True


    error_text = str(
        exception
    ).lower()


    retryable_terms = [
        "quota",
        "rate limit",
        "rate_limit",
        "resource exhausted",
        "resource_exhausted",
        "too many requests",
        "high demand",
        "temporarily unavailable",
    ]


    return any(
        term in error_text
        for term in retryable_terms
    )


# ============================================================
# TOKEN USAGE
# ============================================================

def get_token_usage(response):

    usage = getattr(
        response,
        "usage",
        None,
    )


    if usage is None:
        return 0, 0


    input_tokens = int(
        getattr(
            usage,
            "prompt_tokens",
            0,
        )
        or 0
    )


    output_tokens = int(
        getattr(
            usage,
            "completion_tokens",
            0,
        )
        or 0
    )


    return (
        input_tokens,
        output_tokens,
    )


# ============================================================
# CACHE HIT DETECTION
# ============================================================

def is_cache_hit(response):

    hidden_params = getattr(
        response,
        "_hidden_params",
        {},
    ) or {}


    return bool(
        hidden_params.get(
            "cache_hit",
            False,
        )
    )


# ============================================================
# MAIN LLM CALL
# ============================================================

def call_llm(
    messages,
    simulated_failures=None,
):

    if simulated_failures is None:
        simulated_failures = {}


    last_error = None

    fallback_attempts = 0


    # ========================================================
    # LOOP THROUGH API KEY POOL
    # ========================================================

    for index, api_key in enumerate(
        settings.llm_api_keys
    ):

        key_id = f"key_{index + 1}"


        # ====================================================
        # SIMULATED FAILURE
        # ====================================================

        simulated_status = (
            get_simulated_failure(
                key_id,
                simulated_failures,
            )
        )


        if simulated_status is not None:

            print(
                f"[SIMULATION] "
                f"{key_id} -> "
                f"{simulated_status}"
            )

            fallback_attempts += 1

            continue


        try:

            print(
                f"[LLM] Trying {key_id}"
            )


            # =================================================
            # START TIMER
            # =================================================

            start_time = (
                time.perf_counter()
            )


            # =================================================
            # LITELLM REQUEST
            # =================================================

            response = completion(

                model=
                    settings.llm_model,

                messages=
                    messages,

                api_key=
                    api_key,

                # Built-in LiteLLM caching.
                caching=True,

                # Avoid hanging provider requests.
                timeout=15,

                # We control key fallback ourselves.
                num_retries=0,
            )


            # =================================================
            # LATENCY
            # =================================================

            latency_ms = int(
                (
                    time.perf_counter()
                    - start_time
                )
                * 1000
            )


            # =================================================
            # RESPONSE TEXT
            # =================================================

            reply = (
                response
                .choices[0]
                .message
                .content
            )


            if not reply:

                raise RuntimeError(
                    "provider returned empty response"
                )


            # =================================================
            # TOKEN USAGE
            # =================================================

            (
                input_tokens,
                output_tokens,
            ) = get_token_usage(
                response
            )


            # =================================================
            # CACHE CHECK
            # =================================================

            cache_hit = is_cache_hit(
                response
            )


            # =================================================
            # CACHE RESPONSE
            # =================================================

            if cache_hit:

                print(
                    "[CACHE] LLM_CACHE"
                )


                return {

                    "reply":
                        reply,

                    "model":
                        settings.llm_model,

                    "latency_ms":
                        latency_ms,

                    "input_tokens":
                        input_tokens,

                    "output_tokens":
                        output_tokens,

                    "resolution_source":
                        "LLM_CACHE",

                    # Required by assignment.
                    "key_id":
                        None,

                    # Required by assignment.
                    "fallback_attempts":
                        0,
                }


            # =================================================
            # LIVE RESPONSE
            # =================================================

            print(
                f"[LLM] {key_id} succeeded"
            )


            return {

                "reply":
                    reply,

                "model":
                    settings.llm_model,

                "latency_ms":
                    latency_ms,

                "input_tokens":
                    input_tokens,

                "output_tokens":
                    output_tokens,

                "resolution_source":
                    "LIVE_INFERENCE",

                "key_id":
                    key_id,

                "fallback_attempts":
                    fallback_attempts,
            }


        # ====================================================
        # PROVIDER FAILURE
        # ====================================================

        except Exception as exc:

            last_error = exc


            status_code = (
                get_status_code(
                    exc
                )
            )


            print(
                "\n"
                "============================\n"
                f"[LLM ERROR] {key_id}\n"
                f"Status: {status_code}\n"
                f"Type: {type(exc).__name__}\n"
                f"Error: {exc}\n"
                "============================\n"
            )


            # ------------------------------------------------
            # Required 429/quota/5xx fallback.
            # ------------------------------------------------

            if is_retryable_error(exc):

                fallback_attempts += 1


                print(
                    f"[FAILOVER] "
                    f"{key_id} failed. "
                    f"Trying next key..."
                )


                continue


            # ------------------------------------------------
            # Other provider failures
            # ------------------------------------------------
            #
            # Keep the application resilient and try the next
            # configured key rather than exposing an exception.
            # ------------------------------------------------

            fallback_attempts += 1


            print(
                f"[FAILOVER] "
                f"{key_id} failed. "
                f"Trying next key..."
            )


            continue


    # ========================================================
    # ALL KEYS FAILED
    # ========================================================

    print(
        "\n"
        "============================\n"
        "[LLM ERROR]\n"
        "ALL PROVIDERS UNAVAILABLE\n"
        "============================"
    )


    raise RuntimeError(
        "all providers unavailable"
    ) from last_error