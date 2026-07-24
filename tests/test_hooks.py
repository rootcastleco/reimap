"""Tests for the hook registry — the core extensibility mechanism."""

from __future__ import annotations

import pytest

from reimap.hooks import HookName, HookRegistry


def test_event_hook_runs_subscribers_in_priority_order():
    reg = HookRegistry()
    order: list[str] = []

    reg.register(HookName.SCAN_STARTED, lambda ctx: order.append("b"), priority=200, name="b")
    reg.register(HookName.SCAN_STARTED, lambda ctx: order.append("a"), priority=50, name="a")

    reg.emit(HookName.SCAN_STARTED)
    assert order == ["a", "b"]


def test_event_hook_passes_context():
    reg = HookRegistry()
    received = {}

    @reg.on(HookName.CONNECTION_NEW)
    def _cb(ctx):
        received.update(ctx)

    reg.emit(HookName.CONNECTION_NEW, connection="x", extra=1)
    assert received == {"connection": "x", "extra": 1}


def test_raising_subscriber_is_isolated():
    reg = HookRegistry()
    calls: list[str] = []

    reg.register(HookName.SCAN_STARTED, lambda ctx: (_ for _ in ()).throw(ValueError("boom")))
    reg.register(HookName.SCAN_STARTED, lambda ctx: calls.append("ok"))

    reg.emit(HookName.SCAN_STARTED)  # must not raise
    assert calls == ["ok"]


def test_filter_hook_threads_value():
    reg = HookRegistry()
    reg.register(HookName.FILTER_CONNECTION, lambda v, ctx: v + 1, priority=10)
    reg.register(HookName.FILTER_CONNECTION, lambda v, ctx: v * 2, priority=20)

    assert reg.filter(HookName.FILTER_CONNECTION, 3) == (3 + 1) * 2


def test_filter_hook_drop_short_circuits():
    reg = HookRegistry()
    seen: list[int] = []

    reg.register(HookName.FILTER_CONNECTION, lambda v, ctx: None, priority=10)
    reg.register(HookName.FILTER_CONNECTION, lambda v, ctx: seen.append(v) or v, priority=20)

    assert reg.filter(HookName.FILTER_CONNECTION, 5) is None
    assert seen == []  # second subscriber never ran


def test_unregister_and_clear():
    reg = HookRegistry()

    def cb(ctx):
        pass

    reg.register(HookName.APP_READY, cb)
    assert reg.count() == 1
    assert reg.unregister(HookName.APP_READY, cb) is True
    assert reg.count() == 0

    reg.register(HookName.APP_READY, cb)
    reg.clear()
    assert reg.count() == 0


def test_describe_and_subscribers():
    reg = HookRegistry()
    reg.register(HookName.SCAN_COMPLETED, lambda ctx: None, name="logger")
    assert reg.subscribers(HookName.SCAN_COMPLETED) == ["logger"]
    assert "scan.completed" in reg.describe()


def test_all_hook_names_are_unique_and_stringy():
    names = HookName.all_names()
    assert len(names) == len(set(names))
    assert all(isinstance(n, str) for n in names)


@pytest.mark.parametrize("hook", list(HookName))
def test_every_hook_accepts_string_or_enum(hook):
    reg = HookRegistry()
    reg.register(hook.value, lambda *a: None)  # string form
    reg.register(hook, lambda *a: None)  # enum form
    assert reg.count() == 2
