from src.zyron.core.router import ZyronRouter


def test_clarification_state_is_created():
    router = ZyronRouter(name="Mustaq")

    response, should_exit = router.route(
        "Calculate 10 multiplied",
        name="Mustaq",
    )

    assert should_exit is False
    assert "multiplier" in response
    assert router.agent._pending_clarification is not None

    pending = router.agent._pending_clarification

    assert pending["tool"] == "calculate_scaled_value"
    assert pending["missing_arguments"] == ["multiplier"]
    assert pending["arguments"]["value"] == 10


def test_clarification_executes_after_missing_integer_is_supplied():
    router = ZyronRouter(name="Mustaq")

    response1, should_exit1 = router.route(
        "Calculate 10 multiplied",
        name="Mustaq",
    )

    assert should_exit1 is False
    assert "multiplier" in response1
    assert router.agent._pending_clarification is not None

    response2, should_exit2 = router.route(
        "5",
        name="Mustaq",
    )

    assert should_exit2 is False
    assert "Calculated result: 50" in response2
    assert router.agent._pending_clarification is None


def test_invalid_integer_clarification_does_not_execute():
    router = ZyronRouter(name="Mustaq")

    response1, should_exit1 = router.route(
        "Calculate 10 multiplied",
        name="Mustaq",
    )

    assert should_exit1 is False
    assert "multiplier" in response1
    assert router.agent._pending_clarification is not None

    response2, should_exit2 = router.route(
        "five",
        name="Mustaq",
    )

    assert should_exit2 is False
    assert "must be an integer" in response2
    assert router.agent._pending_clarification is not None


def test_cancel_clears_pending_clarification():
    router = ZyronRouter(name="Mustaq")

    response1, should_exit1 = router.route(
        "Calculate 10 multiplied",
        name="Mustaq",
    )

    assert should_exit1 is False
    assert "multiplier" in response1
    assert router.agent._pending_clarification is not None

    response2, should_exit2 = router.route(
        "cancel",
        name="Mustaq",
    )

    assert should_exit2 is False
    assert "cancelled" in response2.lower()
    assert router.agent._pending_clarification is None


def test_pending_clarification_does_not_execute_before_argument_is_supplied():
    router = ZyronRouter(name="Mustaq")

    response, should_exit = router.route(
        "Calculate 10 multiplied",
        name="Mustaq",
    )

    assert should_exit is False
    assert "Calculated result" not in response
    assert router.agent._pending_clarification is not None


def test_pending_clarification_accepts_zero():
    router = ZyronRouter(name="Mustaq")

    response1, should_exit1 = router.route(
        "Calculate 10 multiplied",
        name="Mustaq",
    )

    assert should_exit1 is False
    assert router.agent._pending_clarification is not None

    response2, should_exit2 = router.route(
        "0",
        name="Mustaq",
    )

    assert should_exit2 is False
    assert "Calculated result: 0" in response2
    assert router.agent._pending_clarification is None


def test_pending_clarification_accepts_negative_integer():
    router = ZyronRouter(name="Mustaq")

    response1, should_exit1 = router.route(
        "Calculate 10 multiplied",
        name="Mustaq",
    )

    assert should_exit1 is False
    assert router.agent._pending_clarification is not None

    response2, should_exit2 = router.route(
        "-5",
        name="Mustaq",
    )

    assert should_exit2 is False
    assert "Calculated result: -50" in response2
    assert router.agent._pending_clarification is None
