"""BDD executável — T04 WorkerLimiter (WL-01..WL-09)."""

from __future__ import annotations

import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, wait

from github_rag.settings import SettingsBootstrapError, load_settings


class TestWL01Defaults(unittest.TestCase):
    def test_defaults_index_2_query_4(self) -> None:
        from github_rag.concurrency.limiter import (
            create_index_limiter,
            create_query_limiter,
        )

        settings = load_settings({})
        index = create_index_limiter(settings)
        query = create_query_limiter(settings)
        self.assertEqual(index.capacity, 2)
        self.assertEqual(query.capacity, 4)


class TestWL02NeverExceeds(unittest.TestCase):
    def test_peak_never_exceeds_capacity(self) -> None:
        from github_rag.concurrency.limiter import SemaphoreWorkerLimiter

        limiter = SemaphoreWorkerLimiter(capacity=2, pool="index")
        peak = 0
        active = 0
        lock = threading.Lock()

        def work() -> None:
            nonlocal peak, active
            with limiter.acquire():
                with lock:
                    active += 1
                    peak = max(peak, active)
                time.sleep(0.05)
                with lock:
                    active -= 1

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(work) for _ in range(4)]
            wait(futures)
            for future in futures:
                future.result()

        self.assertLessEqual(peak, 2)
        self.assertGreaterEqual(peak, 1)


class TestWL03WaitThenRun(unittest.TestCase):
    def test_excess_waits_then_runs(self) -> None:
        from github_rag.concurrency.limiter import SemaphoreWorkerLimiter

        limiter = SemaphoreWorkerLimiter(capacity=1, pool="index")
        second_entered = threading.Event()
        release_first = threading.Event()
        first_acquired = threading.Event()

        def first() -> None:
            with limiter.acquire():
                first_acquired.set()
                release_first.wait(timeout=2.0)
                self.assertTrue(release_first.is_set())

        def second() -> None:
            self.assertTrue(first_acquired.wait(timeout=2.0))
            with limiter.acquire():
                second_entered.set()

        t1 = threading.Thread(target=first)
        t2 = threading.Thread(target=second)
        t1.start()
        self.assertTrue(first_acquired.wait(timeout=2.0))
        t2.start()
        time.sleep(0.05)
        self.assertFalse(second_entered.is_set())
        release_first.set()
        t1.join(timeout=2.0)
        t2.join(timeout=2.0)
        self.assertTrue(second_entered.is_set())


class TestWL04Isolation(unittest.TestCase):
    def test_index_full_does_not_block_query(self) -> None:
        from github_rag.concurrency.limiter import SemaphoreWorkerLimiter

        index = SemaphoreWorkerLimiter(capacity=1, pool="index")
        query = SemaphoreWorkerLimiter(capacity=1, pool="query")
        index_hold = threading.Event()
        index_acquired = threading.Event()
        query_acquired = threading.Event()

        def hold_index() -> None:
            with index.acquire():
                index_acquired.set()
                index_hold.wait(timeout=2.0)

        t = threading.Thread(target=hold_index)
        t.start()
        self.assertTrue(index_acquired.wait(timeout=2.0))
        with query.acquire():
            query_acquired.set()
        self.assertTrue(query_acquired.is_set())
        index_hold.set()
        t.join(timeout=2.0)

    def test_query_full_does_not_block_index(self) -> None:
        from github_rag.concurrency.limiter import SemaphoreWorkerLimiter

        index = SemaphoreWorkerLimiter(capacity=1, pool="index")
        query = SemaphoreWorkerLimiter(capacity=1, pool="query")
        query_hold = threading.Event()
        query_acquired = threading.Event()
        index_acquired = threading.Event()

        def hold_query() -> None:
            with query.acquire():
                query_acquired.set()
                query_hold.wait(timeout=2.0)

        t = threading.Thread(target=hold_query)
        t.start()
        self.assertTrue(query_acquired.wait(timeout=2.0))
        with index.acquire():
            index_acquired.set()
        self.assertTrue(index_acquired.is_set())
        query_hold.set()
        t.join(timeout=2.0)


class TestWL05LimitOneSerializes(unittest.TestCase):
    def test_limit_one_no_overlap(self) -> None:
        from github_rag.concurrency.limiter import SemaphoreWorkerLimiter

        limiter = SemaphoreWorkerLimiter(capacity=1, pool="index")
        intervals: list[tuple[float, float]] = []
        lock = threading.Lock()

        def work() -> None:
            with limiter.acquire():
                start = time.monotonic()
                time.sleep(0.04)
                end = time.monotonic()
                with lock:
                    intervals.append((start, end))

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(work) for _ in range(2)]
            wait(futures)
            for future in futures:
                future.result()

        self.assertEqual(len(intervals), 2)
        a, b = sorted(intervals, key=lambda item: item[0])
        self.assertLessEqual(a[1], b[0] + 1e-3)


class TestWL06Burst(unittest.TestCase):
    def test_burst_respects_capacity(self) -> None:
        from github_rag.concurrency.limiter import SemaphoreWorkerLimiter

        limiter = SemaphoreWorkerLimiter(capacity=3, pool="query")
        peak = 0
        active = 0
        lock = threading.Lock()

        def work() -> None:
            nonlocal peak, active
            with limiter.acquire():
                with lock:
                    active += 1
                    peak = max(peak, active)
                time.sleep(0.02)
                with lock:
                    active -= 1

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(work) for _ in range(10)]
            wait(futures)
            for future in futures:
                future.result()

        self.assertLessEqual(peak, 3)
        self.assertEqual(len(futures), 10)


class TestWL07ReleaseOnException(unittest.TestCase):
    def test_slot_released_after_exception(self) -> None:
        from github_rag.concurrency.limiter import SemaphoreWorkerLimiter

        limiter = SemaphoreWorkerLimiter(capacity=1, pool="index")

        with self.assertRaises(RuntimeError):
            with limiter.acquire():
                raise RuntimeError("boom")

        entered = False
        with limiter.acquire():
            entered = True
        self.assertTrue(entered)


class TestWL08InvalidCapacity(unittest.TestCase):
    def test_zero_capacity_rejected(self) -> None:
        from github_rag.concurrency.limiter import (
            SemaphoreWorkerLimiter,
            WorkerLimiterError,
        )

        with self.assertRaises(WorkerLimiterError):
            SemaphoreWorkerLimiter(capacity=0, pool="index")

    def test_negative_capacity_rejected(self) -> None:
        from github_rag.concurrency.limiter import (
            SemaphoreWorkerLimiter,
            WorkerLimiterError,
        )

        with self.assertRaises(WorkerLimiterError):
            SemaphoreWorkerLimiter(capacity=-1, pool="query")


class TestWL09NonIntegerRemainsT01(unittest.TestCase):
    def test_non_integer_env_raises_settings_bootstrap_error(self) -> None:
        with self.assertRaises(SettingsBootstrapError):
            load_settings({"INDEX_WORKERS": "abc"})


if __name__ == "__main__":
    unittest.main()
