from src.zyron.core.router import ZyronRouter


def test_all_expected_tools_registered():
    router = ZyronRouter(name="Mustaq")

    expected_tools = [
        "calculate_scaled_value",
        "system",
        "application",
        "open_zyron_folder",
        "list_zyron_files",
        "create_folder",
        "create_file",
        "write_file",
        "open_file",
        "read_file",
        "delete_item",
        "rename_item",
        "web_search",
    ]

    registered_tools = router.registry.get_names()

    missing_tools = [
        tool
        for tool in expected_tools
        if tool not in registered_tools
    ]

    assert not missing_tools, (
        f"Missing registered tools: {missing_tools}"
    )


def test_expected_tool_count():
    router = ZyronRouter(name="Mustaq")

    expected_tools = [
        "calculate_scaled_value",
        "system",
        "application",
        "open_zyron_folder",
        "list_zyron_files",
        "create_folder",
        "create_file",
        "write_file",
        "open_file",
        "read_file",
        "delete_item",
        "rename_item",
        "web_search",
    ]

    registered_tools = router.registry.get_names()

    assert len(registered_tools) == len(expected_tools)


def test_capability_discovery():
    router = ZyronRouter(name="Mustaq")

    discovery_tests = [
        (
            "Calculate 10 multiplied by 5",
            "calculate_scaled_value",
        ),
        (
            "What is in my Zyron folder?",
            "list_zyron_files",
        ),
        (
            "Create a folder called TestFolder",
            "create_folder",
        ),
        (
            "Create a file called test.txt",
            "create_file",
        ),
        (
            "Read the file test.txt",
            "read_file",
        ),
    ]

    for command, expected_tool in discovery_tests:
        candidates = (
            router.agent._find_candidate_capabilities(
                command
            )
        )

        assert expected_tool in candidates, (
            f"Command '{command}' did not discover "
            f"'{expected_tool}'. Candidates: {candidates}"
        )


def test_missing_argument_is_rejected():
    router = ZyronRouter(name="Mustaq")

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


def test_complete_arguments_are_accepted():
    router = ZyronRouter(name="Mustaq")

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
