from src.zyron.core.router import ZyronRouter


def calculate_scaled_value(
    value: int,
    multiplier: int,
):
    return f"Calculated result: {value * multiplier}"


router = ZyronRouter(name="Mustaq")

router.registry.register(
    name="calculate_scaled_value",
    description=(
        "Calculate a value multiplied by a multiplier. "
        "Required arguments: value and multiplier."
    ),
    function=calculate_scaled_value,
)


command = "Calculate 10 multiplied"

print("=== PHASE 5 - REQUIRED ARGUMENT VALIDATION TEST ===")
print()

print("COMMAND:")
print(command)
print()

print("PLAN:")
plan = router.agent.create_plan(command)
print(plan)
print()

print("ROUTE:")
response, should_exit = router.route(
    command,
    name="Mustaq",
)

print(response)
print()

print("SHOULD EXIT:")
print(should_exit)
