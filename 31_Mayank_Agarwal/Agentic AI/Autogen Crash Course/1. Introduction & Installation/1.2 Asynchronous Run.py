import asyncio
import time

async def brew_coffee():
    print("Starting Brewing Coffee")
    await asyncio.sleep(3)
    print("Coffee Ready")

async def toast_bagel():
    print("Start Toasting bagel")
    await asyncio.sleep(2)
    print("Bagel Ready")


async def main():
    start = time.time()

    coffee = brew_coffee()
    bagel = toast_bagel()

    results = await asyncio.gather(coffee,bagel)

    end = time.time()

    print(f"Time : {end - start:.2f} minutes")


asyncio.run(main())