from src.zyron.core.router import ZyronRouter


def fake_action(
    recipient: str,
    subject: str,
    body: str,
):
    return (
        f"Action executed for {recipient}: "
        f"{subject} / {body}"
    )


def build_router():
    router = ZyronRouter(name="Mustaq")

    router.registry.register(
        name="fake_action",
        description=(
            "Perform an action using a recipient, subject, "
            "and body. All three arguments are required."
        ),
        function=fake_action,
    )

    return router


def test_multiple_missing_arguments_are_stored():
    router = build_router()

    router.agent._pending_clarification = {
        "command": "Perform the action for test@example.com",
        "tool": "fake_action",
        "arguments": {
            "recipient": "test@example.com",
        },
        "missing_arguments": [
            "subject",
            "body",
        ],
    }

    assert router.agent._pending_clarification is not None

    pending = router.agent._pending_clarification

    assert pending["tool"] == "fake_action"
    assert pending["arguments"]["recipient"] == "test@example.com"
    assert pending["missing_arguments"] == [
        "subject",
        "body",
    ]


def test_first_clarification_fills_subject_and_keeps_body_pending():
    router = build_router()

    router.agent._pending_clarification = {
        "command": "Perform the action for test@example.com",
        "tool": "fake_action",
        "arguments": {
            "recipient": "test@example.com",
        },
        "missing_arguments": [
            "subject",
            "body",
        ],
    }

    response = router.agent._clarification_reply(
        "Hello"
    )

    assert response is not None
    assert "body" in response
    assert router.agent._pending_clarification is not None

    pending = router.agent._pending_clarification

    assert pending["arguments"]["recipient"] == "test@example.com"
    assert pending["arguments"]["subject"] == "Hello"
    assert pending["missing_arguments"] == [
        "body",
    ]


def test_second_clarification_completes_request():
    router = build_router()

    router.agent._pending_clarification = {
        "command": "Perform the action for test@example.com",
        "tool": "fake_action",
        "arguments": {
            "recipient": "test@example.com",
            "subject": "Hello",
        },
        "missing_arguments": [
            "body",
        ],
    }

    response = router.agent._clarification_reply(
        "This is a test"
    )

    assert response is not None
    assert "Action executed" in response

    assert router.agent._pending_clarification is None


def test_multiple_argument_clarification_end_to_end():
    router = build_router()

    response1, exit1 = router.route(
        "Perform the action for test@example.com",
        name="Mustaq",
    )

    assert exit1 is False
    assert "subject" in response1
    assert "body" in response1
    assert router.agent._pending_clarification is not None

    response2, exit2 = router.route(
        "Hello",
        name="Mustaq",
    )

    assert exit2 is False
    assert "body" in response2
    assert router.agent._pending_clarification is not None

    response3, exit3 = router.route(
        "This is a test",
        name="Mustaq",
    )

    assert exit3 is False
    assert "Action executed" in response3
    assert router.agent._pending_clarification is None
