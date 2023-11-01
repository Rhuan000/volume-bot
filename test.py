import asyncio

async def loop1():
    while True:
        print("Loop 1 is running")
        await asyncio.sleep(1)

async def loop2():
    while True:
        print("Loop 2 is running")
        await asyncio.sleep(2)

async def loop3():
    while True:
        print("Loop 3 is running")
        await asyncio.sleep(3)

async def loop4():
    while True:
        print("Loop 4 is running")
        await asyncio.sleep(4)

async def main():
    task1 = asyncio.create_task(loop1())
    task2 = asyncio.create_task(loop2())
    task3 = asyncio.create_task(loop3())

    await asyncio.sleep(5)  # Let the first three loops run for 5 seconds

    task4 = asyncio.create_task(loop4())  # Start the fourth loop

    await asyncio.gather(task1, task2, task3, task4)

if __name__ == "__main__":
    asyncio.run(main())
