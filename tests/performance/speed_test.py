import time

from src.zyron.core.router import ZyronRouter


router = ZyronRouter(name="Mustaq")


tests = [
    "Open Chrome.",
    "How hard is my processor working right now?",
    "What is my CPU usage?",
    "Create a folder called TestFolder",
    "Open the Zyron folder",
    "What do you remember about me?",
    "Hello Zyron, how are you?",
]


print()
print("==============================")
print("       ZYRON SPEED TEST")
print("==============================")
print()


for command in tests:

    print(f"Command: {command}")

    start = time.perf_counter()

    response, should_exit = router.route(
        command,
        name="Mustaq",
    )

    elapsed = time.perf_counter() - start

    print(f"Response: {response}")
    print(f"Time: {elapsed:.2f} seconds")
    print("-" * 50)