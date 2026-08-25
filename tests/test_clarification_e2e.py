from src.zyron.core.router import ZyronRouter


router = ZyronRouter(name="Mustaq")


print("============================================================")
print("ZYRON CLARIFICATION END-TO-END TEST")
print("============================================================")
print()


print("STEP 1")
print("USER: Calculate 10 multiplied")
print()

response1, exit1 = router.route(
    "Calculate 10 multiplied",
    name="Mustaq",
)

print("ZYRON:")
print(response1)
print()
print("EXIT:", exit1)
print()


print("STEP 2")
print("USER: 5")
print()

response2, exit2 = router.route(
    "5",
    name="Mustaq",
)

print("ZYRON:")
print(response2)
print()
print("EXIT:", exit2)
print()


print("============================================================")
print("EXPECTED")
print("============================================================")
print()
print("Step 1 should ask for the multiplier.")
print("Step 2 should execute calculate_scaled_value.")
print("Expected result: 50")
print()
