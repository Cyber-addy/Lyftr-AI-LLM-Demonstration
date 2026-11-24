from contextlib import asynccontextmanager

import json


from fastapi import (
    FastAPI,
    HTTPException,
    Header,
)


from fastapi.middleware.cors import (
    CORSMiddleware,
)


from sqlalchemy import text


from app.config import settings


from app.database import (
    create_tables,
    SessionLocal,
    Message,
)


from app.schemas import (
    ChatRequest,
)


from app.services.llm_service import (
    call_llm,
)


from app.services.failure_simulator import (
    parse_failure_header,
)


# ============================================================
# DEFAULT SYSTEM PROMPT
# ============================================================

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful AI assistant."
)


# ============================================================
# APPLICATION STARTUP
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    create_tables()

    yield


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Lyftr AI Backend",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=
        settings.allowed_origins,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# HEALTH ENDPOINT
# ============================================================

@app.get("/health")
def health():

    db = SessionLocal()


    try:

        # Verify SQLite connectivity.
        db.execute(
            text("SELECT 1")
        )


    except Exception:

        raise HTTPException(
            status_code=503,
            detail="database unavailable",
        )


    finally:

        db.close()


    return {

        "status":
            "ok",

        "keys_configured":
            len(
                settings.llm_api_keys
            ),

        "cache_enabled":
            True,
    }


# ============================================================
# CHAT ENDPOINT
# ============================================================

@app.post("/chat")
def chat(

    request: ChatRequest,

    x_simulate_failure: str | None = Header(
        default=None,
        alias="X-Simulate-Failure",
    ),

):

    db = SessionLocal()


    try:

        # ====================================================
        # FAILURE SIMULATION
        # ====================================================

        simulated_failures = {}


        if (
            settings.enable_failure_simulation
            and x_simulate_failure
        ):

            simulated_failures = (
                parse_failure_header(
                    x_simulate_failure
                )
            )


        # ====================================================
        # LOAD EXISTING SESSION HISTORY
        # ====================================================

        history = (

            db.query(Message)

            .filter(
                Message.session_id
                == request.session_id
            )

            .order_by(
                Message.id.asc()
            )

            .all()
        )


        # ====================================================
        # BUILD COMPLETE LLM MESSAGE LIST
        # ====================================================

        messages = [

            {
                "role":
                    "system",

                "content":
                    request.system_prompt
                    or DEFAULT_SYSTEM_PROMPT,
            }

        ]


        # Add previous conversation.
        for item in history:

            messages.append(

                {
                    "role":
                        item.role,

                    "content":
                        item.content,
                }

            )


        # Add ONLY the new user message.
        messages.append(

            {
                "role":
                    "user",

                "content":
                    request.message,
            }

        )


        # ====================================================
        # CALL LLM
        # ====================================================

        try:

            result = call_llm(

                messages,

                simulated_failures=
                    simulated_failures,

            )


        except RuntimeError:

            # Failed requests must not be stored.
            db.rollback()


            raise HTTPException(

                status_code=503,

                detail=
                    "all providers unavailable",

            )


        # ====================================================
        # RESPONSE METADATA
        # ====================================================

        metadata = {

            "resolution_source":
                result[
                    "resolution_source"
                ],

            "model":
                result[
                    "model"
                ],

            "latency_ms":
                int(
                    result[
                        "latency_ms"
                    ]
                ),

            "input_tokens":
                int(
                    result[
                        "input_tokens"
                    ]
                ),

            "output_tokens":
                int(
                    result[
                        "output_tokens"
                    ]
                ),

            "key_id":
                result[
                    "key_id"
                ],

            "fallback_attempts":
                int(
                    result[
                        "fallback_attempts"
                    ]
                ),
        }


        # ====================================================
        # SAVE USER MESSAGE
        # ====================================================

        user_message = Message(

            session_id=
                request.session_id,

            role=
                "user",

            content=
                request.message,

            metadata_json=
                None,

        )


        db.add(
            user_message
        )


        # ====================================================
        # SAVE ASSISTANT MESSAGE
        # ====================================================

        assistant_message = Message(

            session_id=
                request.session_id,

            role=
                "assistant",

            content=
                result["reply"],

            metadata_json=
                json.dumps(
                    metadata
                ),

        )


        db.add(
            assistant_message
        )


        # Store user + assistant together.
        db.commit()


        # ====================================================
        # RETURN EXACT API RESPONSE
        # ====================================================

        return {

            "session_id":
                request.session_id,

            "reply":
                result[
                    "reply"
                ],

            "metadata":
                metadata,

        }


    # ========================================================
    # EXPECTED HTTP ERROR
    # ========================================================

    except HTTPException:

        db.rollback()

        raise


    # ========================================================
    # UNEXPECTED ERROR
    # ========================================================

    except Exception as exc:

        db.rollback()


        print(
            f"[CHAT ERROR] "
            f"{type(exc).__name__}: "
            f"{exc}"
        )


        # Never expose stack traces/provider errors.
        raise HTTPException(

            status_code=503,

            detail=
                "all providers unavailable",

        )


    finally:

        db.close()


# ============================================================
# SESSION HISTORY ENDPOINT
# ============================================================

@app.get(
    "/sessions/{session_id}/messages"
)
def get_session_messages(
    session_id: str,
):

    db = SessionLocal()


    try:

        history = (

            db.query(Message)

            .filter(
                Message.session_id
                == session_id
            )

            .order_by(
                Message.id.asc()
            )

            .all()
        )


        # Unknown session.
        if not history:

            raise HTTPException(

                status_code=404,

                detail=
                    "session not found",

            )


        messages = []


        # ====================================================
        # FORMAT HISTORY
        # ====================================================

        for item in history:

            message = {

                "role":
                    item.role,

                "content":
                    item.content,

            }


            # Metadata belongs only to assistant messages.
            if (
                item.role == "assistant"
                and item.metadata_json
            ):

                try:

                    message["metadata"] = (
                        json.loads(
                            item.metadata_json
                        )
                    )


                except json.JSONDecodeError:

                    message["metadata"] = {}


            messages.append(
                message
            )


        return {

            "session_id":
                session_id,

            "messages":
                messages,

        }


    finally:

        db.close()