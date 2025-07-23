import asyncio
import httpx
from collections import Counter
import time


API_BASE_URL = "http://localhost:8000"
ITEM_ID = "charizard-1st-ed"
STATUS_URL = f"{API_BASE_URL}/status/{ITEM_ID}"
PURCHASE_URL = f"{API_BASE_URL}/buy/{ITEM_ID}"
RESET_URL = f"{API_BASE_URL}/reset"
NUM_REQUESTS = 100

# makes a single asynchronous request to the /buy endpoint.
async def make_purchase_request(client: httpx.AsyncClient):
  
    try:
        response = await client.post(PURCHASE_URL, timeout=15.0)
        return response.status_code
    except Exception as e:
        print(f"A request failed: {e}")
        return 500

async def main():
    print(f"\nConcurrency Test")
      # check current state and reset if necessary
    async with httpx.AsyncClient() as client:
        print(f"\n1. Checking current item status")
        try:
            status_response = await client.get(STATUS_URL)
            current_quantity = status_response.json().get('quantity', -1)
            print(f"   Current quantity is: {current_quantity}")

            # we can also comment this part if we have to see the req fails, if the requested item is unavailable.
            if current_quantity == 0:
                print("   Item is sold out. Resetting demo state...")
                await client.post(RESET_URL)
                print("   Reset successful.")

        except httpx.ConnectError:
            print("Fatal: Could not connect to the backend. Is it running?")
            return

        # run the concurrent requests
        print(f"\n2. Firing {NUM_REQUESTS} concurrent purchase requests...")
        start_time = time.time()
        tasks = [make_purchase_request(client) for _ in range(NUM_REQUESTS)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        print(f"   All requests completed in {end_time - start_time:.2f} seconds.")


    print("\n3. Analyzing results...")
    status_counts = Counter(results)
    success_count = status_counts.get(200, 0)
    conflict_count = status_counts.get(409, 0)

    print("\n Test Result Summary ")
    print(f"Total Requests Sent: {len(results)}")
    print(f"Successful Purchases (200 OK): {success_count}")
    print(f"Rejected as Sold Out (409 Conflict): {conflict_count}")
    
    # report any other unexpected status codes
    for status, count in status_counts.items():
        if status not in [200, 409]:
            print(f"Unexpected Status {status}: {count}")
    print("=============================\n")

    if success_count == 1 and conflict_count == NUM_REQUESTS - 1:
        print("SUCCESS: The test passed!")
    else:
        print("FAILURE: The test failed.")

if __name__ == "__main__":
    asyncio.run(main())
