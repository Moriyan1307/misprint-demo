# Marketplace Concurrency PoC

This project is a full-stack proof-of-concept (PoC) demonstrating a robust solution to the "last item" race condition problem common in e-commerce and marketplace applications. It simulates a high-concurrency scenario where multiple users attempt to buy a single available item simultaneously, ensuring only one purchase succeeds while providing a real-time, responsive user experience.

---

## 🚩 The Problem: Race Conditions

In a typical marketplace, if two users try to buy the last available item at the same time, a naive implementation might lead to critical errors:

- **Overselling:** Both users successfully purchase the item, resulting in a negative inventory and a failed order fulfillment.
- **Data Corruption:** The database state becomes inconsistent.
- **Poor User Experience:** One or both users might see a confusing error message after their payment has already been processed.

This project solves this by ensuring that the process of checking availability and updating inventory is **atomic**—an indivisible operation that can only be performed by one user at a time.

---

## 🛠️ The Solution: Pessimistic Locking & Live Updates

This PoC implements a modern, scalable solution using two key principles:

1. **Database-Level Pessimistic Locking:**

   - The system uses PostgreSQL's `SELECT ... FOR UPDATE` statement. When a user attempts a purchase, the application places an exclusive lock on the specific item's row in the database. Any other concurrent attempts to purchase that same item are forced by the database to wait until the first transaction is complete. This "first-come, first-served" approach at the database level is the definitive way to prevent race conditions.

2. **Real-Time Frontend Updates:**
   - To ensure the user interface is always up-to-date, the backend uses **Server-Sent Events (SSE)**. The moment an item is sold or its state is reset, the server pushes an update to all connected web clients, which then instantly re-render to reflect the new inventory status without needing a manual page refresh.

---

## 🧰 Tech Stack

- **Backend:** Python, FastAPI, `asyncpg`
- **Frontend:** Next.js, React, Tailwind CSS
- **Database:** PostgreSQL
- **Containerization:** Docker, Docker Compose
- **Concurrency Test:** Python, `httpx`, `asyncio`

---

## 🚀 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop/) must be installed and running on your machine.

### 1. Clone the Repository

```bash
git clone https://github.com/Moriyan1307/misprint-demo.git
cd misprint-demo
```

### 2. Configuration

- The `docker-compose.yml` file is already set up to read from this directory structure.

### 3. Run the Application

With Docker running, start the entire full-stack application with a single command from the project root:

```bash
docker-compose up --build
```

This will:

- Build the Docker images for the frontend and backend.
- Start the PostgreSQL, backend, and frontend containers.

Your services will be available at:

- **Frontend Application:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000)

### 4. Run the Concurrency Test

To simulate the high-concurrency "stampede," run the test script from the project root in a new terminal window.

First, ensure you have the required Python library:

```bash
pip install httpx
```

Then, run the test:

```bash
python tests/concurrency_test.py
```

Watch the terminal output and the frontend at [http://localhost:3000](http://localhost:3000) to see the results in real-time. The test will show that exactly 1 request succeeds and 99 fail, and the frontend will instantly update to show "Quantity: 0".

---

## 📁 Project Structure

```text
misprint-demo/
│
├── .gitignore              # Ignores unnecessary files
├── docker-compose.yml      # Orchestrates all services
├── README.md               # You are here
│
├── backend/                # FastAPI application
│   ├── Dockerfile
│   └── main.py
│
├── frontend/               # Next.js application
│   ├── Dockerfile
│   └── app/
│
└── tests/                  # Concurrency test script
    └── concurrency_test.py
```
