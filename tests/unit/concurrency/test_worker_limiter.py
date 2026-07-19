"""Testes unitários — WorkerLimiter (T04), extremos e corner cases."""

from __future__ import annotations

import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, wait
from types import SimpleNamespace

from github_rag.concurrency.limiter import (
    SemaphoreWorkerLimiter,
    WorkerLimiter,
    WorkerLimiterError,
    create_index_limiter,
    create_query_limiter,
)


def _settings(*, index_workers: int = 2, query_workers: int = 4) -> SimpleNamespace:
    return SimpleNamespace(index_workers=index_workers, query_workers=query_workers)


class TestCapacityContract(unittest.TestCase):
    def test_u01_capacity_exposed(self) -> None:
        limiter = SemaphoreWorkerLimiter(capacity=3, pool="index")
        self.assertEqual(limiter.capacity, 3)

    def test_u13_protocol_runtime(self) -> None:
        limiter = SemaphoreWorkerLimiter(capacity=1, pool="query")
        self.assertIsInstance(limiter, WorkerLimiter)


class TestConcurrencyLimits(unittest.TestCase):
    def test_u02_peak_never_exceeds_capacity(self) -> None:
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
                time.sleep(0.04)
                with lock:
                    active -= 1

        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [pool.submit(work) for _ in range(6)]
            wait(futures)
            for future in futures:
                future.result()

        self.assertLessEqual(peak, 2)
        self.assertGreaterEqual(peak, 2)

    def test_u03_waiter_blocks_until_release(self) -> None:
        limiter = SemaphoreWorkerLimiter(capacity=1, pool="index")
        first_in = threading.Event()
        release_first = threading.Event()
        second_in = threading.Event()

        def first() -> None:
            with limiter.acquire():
                first_in.set()
                release_first.wait(timeout=2.0)

        def second() -> None:
            self.assertTrue(first_in.wait(timeout=2.0))
            with limiter.acquire():
                second_in.set()

        t1 = threading.Thread(target=first)
        t2 = threading.Thread(target=second)
        t1.start()
        self.assertTrue(first_in.wait(timeout=2.0))
        t2.start()
        time.sleep(0.05)
        self.assertFalse(second_in.is_set())
        release_first.set()
        t1.join(timeout=2.0)
        t2.join(timeout=2.0)
        self.assertTrue(second_in.is_set())

    def test_u04_capacity_one_serializes(self) -> None:
        limiter = SemaphoreWorkerLimiter(capacity=1, pool="query")
        intervals: list[tuple[float, float]] = []
        lock = threading.Lock()

        def work() -> None:
            with limiter.acquire():
                start = time.monotonic()
                time.sleep(0.03)
                end = time.monotonic()
                with lock:
                    intervals.append((start, end))

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(work) for _ in range(2)]
            wait(futures)
            for future in futures:
                future.result()

        a, b = sorted(intervals, key=lambda item: item[0])
        self.assertLessEqual(a[1], b[0] + 1e-3)

    def test_u05_burst_respects_capacity(self) -> None:
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
                time.sleep(0.01)
                with lock:
                    active -= 1

        with ThreadPoolExecutor(max_workers=20) as pool:
            futures = [pool.submit(work) for _ in range(20)]
            wait(futures)
            for future in futures:
                future.result()

        self.assertLessEqual(peak, 2)
        self.assertEqual(len(futures), 20)


class TestFailureAndRelease(unittest.TestCase):
    def test_u06_exception_releases_slot(self) -> None:
        limiter = SemaphoreWorkerLimiter(capacity=1, pool="index")
        with self.assertRaises(ValueError):
            with limiter.acquire():
                raise ValueError("fail")
        with limiter.acquire():
            held = True
        self.assertTrue(held)

    def test_u14_sequential_reacquire_same_thread(self) -> None:
        limiter = SemaphoreWorkerLimiter(capacity=1, pool="query")
        with limiter.acquire():
            pass
        with limiter.acquire():
            ok = True
        self.assertTrue(ok)


class TestInvalidCapacity(unittest.TestCase):
    def test_u07_zero_rejected(self) -> None:
        with self.assertRaises(WorkerLimiterError):
            SemaphoreWorkerLimiter(capacity=0, pool="index")

    def test_u08_negative_rejected(self) -> None:
        with self.assertRaises(WorkerLimiterError):
            SemaphoreWorkerLimiter(capacity=-5, pool="query")

    def test_u15_error_message_cites_pool_and_value(self) -> None:
        with self.assertRaises(WorkerLimiterError) as ctx:
            SemaphoreWorkerLimiter(capacity=0, pool="index")
        message = str(ctx.exception)
        self.assertIn("index", message)
        self.assertIn("0", message)
        self.assertIn(">=", message)


class TestFactories(unittest.TestCase):
    def test_u09_index_factory_uses_settings(self) -> None:
        limiter = create_index_limiter(_settings(index_workers=5, query_workers=9))
        self.assertEqual(limiter.capacity, 5)

    def test_u10_query_factory_uses_settings(self) -> None:
        limiter = create_query_limiter(_settings(index_workers=5, query_workers=9))
        self.assertEqual(limiter.capacity, 9)

    def test_u11_isolation_index_full_query_ok(self) -> None:
        index = create_index_limiter(_settings(index_workers=1, query_workers=1))
        query = create_query_limiter(_settings(index_workers=1, query_workers=1))
        hold = threading.Event()
        index_ready = threading.Event()

        def occupy_index() -> None:
            with index.acquire():
                index_ready.set()
                hold.wait(timeout=2.0)

        t = threading.Thread(target=occupy_index)
        t.start()
        self.assertTrue(index_ready.wait(timeout=2.0))
        with query.acquire():
            query_ok = True
        self.assertTrue(query_ok)
        hold.set()
        t.join(timeout=2.0)

    def test_u16_isolation_query_full_index_ok(self) -> None:
        index = create_index_limiter(_settings(index_workers=1, query_workers=1))
        query = create_query_limiter(_settings(index_workers=1, query_workers=1))
        hold = threading.Event()
        query_ready = threading.Event()

        def occupy_query() -> None:
            with query.acquire():
                query_ready.set()
                hold.wait(timeout=2.0)

        t = threading.Thread(target=occupy_query)
        t.start()
        self.assertTrue(query_ready.wait(timeout=2.0))
        with index.acquire():
            index_ok = True
        self.assertTrue(index_ok)
        hold.set()
        t.join(timeout=2.0)

    def test_u12_factory_rejects_zero_without_fallback(self) -> None:
        with self.assertRaises(WorkerLimiterError):
            create_index_limiter(_settings(index_workers=0))
        with self.assertRaises(WorkerLimiterError):
            create_query_limiter(_settings(query_workers=-1))


class TestObservabilityCounters(unittest.TestCase):
    """T26 / UT-L01..L04 — active/waiting/peak_active."""

    def test_ut_l01_peak_active_under_saturation(self) -> None:
        limiter = SemaphoreWorkerLimiter(capacity=2, pool="query")
        release = threading.Event()

        def work() -> None:
            with limiter.acquire():
                release.wait(timeout=5.0)

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(work) for _ in range(4)]
            time.sleep(0.1)
            self.assertLessEqual(limiter.peak_active, 2)
            release.set()
            wait(futures)
            for future in futures:
                future.result()
        self.assertLessEqual(limiter.peak_active, 2)
        self.assertGreaterEqual(limiter.peak_active, 1)

    def test_ut_l02_waiting_under_saturation(self) -> None:
        limiter = SemaphoreWorkerLimiter(capacity=1, pool="query")
        release = threading.Event()
        entered = threading.Event()

        def holder() -> None:
            with limiter.acquire():
                entered.set()
                release.wait(timeout=5.0)

        def waiter() -> None:
            with limiter.acquire():
                pass

        t1 = threading.Thread(target=holder)
        t2 = threading.Thread(target=waiter)
        t1.start()
        self.assertTrue(entered.wait(timeout=2.0))
        t2.start()
        time.sleep(0.05)
        self.assertGreaterEqual(limiter.waiting, 1)
        release.set()
        t1.join(timeout=2.0)
        t2.join(timeout=2.0)

    def test_ut_l03_active_and_waiting_zero_after_release(self) -> None:
        limiter = SemaphoreWorkerLimiter(capacity=2, pool="query")
        with limiter.acquire():
            self.assertEqual(limiter.active, 1)
        self.assertEqual(limiter.active, 0)
        self.assertEqual(limiter.waiting, 0)

    def test_ut_l04_exception_resets_counters(self) -> None:
        limiter = SemaphoreWorkerLimiter(capacity=1, pool="query")
        with self.assertRaises(RuntimeError):
            with limiter.acquire():
                self.assertEqual(limiter.active, 1)
                raise RuntimeError("boom")
        self.assertEqual(limiter.active, 0)
        self.assertEqual(limiter.waiting, 0)
        with limiter.acquire():
            self.assertEqual(limiter.active, 1)


if __name__ == "__main__":
    unittest.main()
