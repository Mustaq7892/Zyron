from src.zyron.core.router import ZyronRouter


def calculate_scaled_value(
    value: int,
    multiplier: int,
):
    return f"Calculated result: {value * multiplier}"


def fake_action(
    recipient: str,
    subject: str,
    body: str,
):
    return "Action executed."


def build_router():
    router = ZyronRouter(name="Mustaq")

    router.registry.register(
        name="calculate_scaled_value",
        description=(
            "Calculate a numeric value multiplied by another "
            "numeric value. Required arguments: value and "
            "multiplier."
        ),
        function=calculate_scaled_value,
    )

    router.registry.register(
        name="fake_action",
        description=(
            "Perform an action using a recipient, subject, "
            "and body. All three arguments are required."
        ),
        function=fake_action,
    )

    return router


def test_missing_single_required_argument():
    router = build_router()

    missing = (
        router.agent._find_missing_required_arguments(
            "calculate_scaled_value",
            {
                "value": 10,
            },
        )
    )

    assert missing == [
        "multiplier"
    ]


def test_missing_multiple_required_arguments():
    router = build_router()

    missing = (
        router.agent._find_missing_required_arguments(
            "fake_action",
            {
                "recipient": "test@example.com",
            },
        )
    )

    assert missing == [
        "subject",
        "body",
    ]


def test_all_required_arguments_present():
    router = build_router()

    missing = (
        router.agent._find_missing_required_arguments(
            "calculate_scaled_value",
            {
                "value": 10,
                "multiplier": 5,
            },
        )
    )

    assert missing == []


def test_empty_required_argument_is_missing():
    router = build_router()

    missing = (
        router.agent._find_missing_required_arguments(
            "fake_action",
            {
                "recipient": "test@example.com",
                "subject": "",
                "body": "Test",
            },
        )
    )

    assert missing == [
        "subject"
    ]


def test_unknown_argument_is_rejected():
    router = build_router()

    validation = (
        router.agent._validate_plan_arguments(
            "calculate_scaled_value",
            {
                "value": 10,
                "multiplier": 5,
                "unexpected": 99,
            },
            "Calculate 10 multiplied by 5",
        )
    )

    assert validation["valid"] is False
    assert "Unknown argument" in validation["error"]


def test_wrong_argument_type_is_rejected():
    router = build_router()

    validation = (
        router.agent._validate_plan_arguments(
            "calculate_scaled_value",
            {
                "value": "10",
                "multiplier": 5,
            },
            "Calculate 10 multiplied by 5",
        )
    )

    assert validation["valid"] is False
    assert "must be an integer" in validation["error"]


def test_invented_numeric_argument_is_rejected():
    router = build_router()

    validation = (
        router.agent._validate_plan_arguments(
            "calculate_scaled_value",
            {
                "value": 10,
                "multiplier": 1,
            },
            "Calculate 10 multiplied",
        )
    )

    assert validation["valid"] is False
    assert "not grounded" in validation["error"]


def test_supplied_numeric_arguments_are_accepted():
    router = build_router()

    validation = (
        router.agent._validate_plan_arguments(
            "calculate_scaled_value",
            {
                "value": 10,
                "multiplier": 5,
            },
            "Calculate 10 multiplied by 5",
        )
    )

    assert validation["valid"] is True


def test_missing_argument_blocks_tool_execution():
    router = build_router()

    plan = router.agent._normalize_plan(
        {
            "needs_tools": True,
            "plan": [
                {
                    "tool": "calculate_scaled_value",
                    "arguments": {
                        "value": 10,
                        "multiplier": 1,
                    },
                }
            ],
            "response": "",
        },
        "Calculate 10 multiplied",
    )

    assert plan["needs_tools"] is False
    assert plan["plan"] == []
    assert "multiplier" in plan["response"]


def test_complete_plan_remains_executable():
    router = build_router()

    plan = router.agent._normalize_plan(
        {
            "needs_tools": True,
            "plan": [
                {
                    "tool": "calculate_scaled_value",
                    "arguments": {
                        "value": 10,
                        "multiplier": 5,
                    },
                }
            ],
            "response": "",
        },
        "Calculate 10 multiplied by 5",
    )

    assert plan["needs_tools"] is True
    assert len(plan["plan"]) == 1
    assert (
        plan["plan"][0]["tool"]
        == "calculate_scaled_value"
    )
    assert (
        plan["plan"][0]["arguments"]
        == {
            "value": 10,
            "multiplier": 5,
        }
    )


def test_clarification_for_multiple_missing_arguments():
    router = build_router()

    response = (
        router.agent._create_missing_argument_clarification(
            "fake_action",
            [
                "subject",
                "body",
            ],
        )
    )

    assert (
        response
        == (
            "I need 'subject' and 'body' before I can use "
            "'fake_action'. Please provide them."
        )
    )
