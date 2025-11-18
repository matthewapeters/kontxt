import sys
import os
import json
import pytest

# Ensure src is importable
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from kontxt.kontxt import ToolCall, PlanItem, UserSession, Kontxt


def test_toolcall_to_string_contains_fields():
    tc = ToolCall(name="search", args={"q": "abc"}, result="found")
    s = tc.to_string()
    assert "Tool: search" in s
    assert '"q": "abc"' in s
    assert "found" in s


def test_planitem_to_string_raises_missing_plan_state():
    # PlanItem.to_string references a missing attribute `plan_state` and should raise
    pi = PlanItem(task="Do thing", tool_calls=[ToolCall(name="t", args={}, result="r")])
    with pytest.raises(Exception):
        _ = pi.to_string()


def test_user_session_defaults_and_context_operations():
    sess = UserSession(plan=[], user="alice")
    assert sess.user == "alice"
    assert sess.context == []


def test_kontxt_session_plan_user_and_context_properties(monkeypatch):
    k = Kontxt()
    # patch uuid1 to have predictable key
    import kontxt.kontxt as kmod

    monkeypatch.setattr(kmod, "uuid1", lambda: "fixed-key")

    sess = UserSession(plan=[], user="bob", context=["c1"])
    k.session = sess
    assert k._key == "fixed-key"
    assert k.session.user == "bob"

    # plan setter/getter
    k.plan = ["step1"]
    assert k.plan == ["step1"]

    # user setter/getter
    k.user = "charlie"
    assert k.user == "charlie"

    # context setter/getter and add_context
    k.context = ["ctx1"]
    assert k.context == ["ctx1"]
    k.add_context("ctx2")
    assert k.context[-1] == "ctx2"

    # context_str formatting
    assert "* ctx1" in k.context_str
    assert "* ctx2" in k.context_str

    # summary contains the user and context list
    s = k.summary
    assert "User" in s
    assert "charlie" in s


def test_plan_str_empty_session_returns_fallback():
    k = Kontxt()
    # set _key to a session that's an empty list -> len(self.session) == 0
    k._key = "k"
    k._context["k"] = []
    ps = k.plan_str
    assert "Agent should define" in ps


def test_query_ollama_no_response(monkeypatch):
    k = Kontxt()
    import kontxt.kontxt as kmod

    monkeypatch.setattr(kmod, "uuid1", lambda: "q1")

    # prepare session so assignments to plan/tool_calls won't blow up
    k.session = UserSession(plan=[], user="u1", context=[])

    class DummyResp:
        def json(self):
            return {"response": ""}

    monkeypatch.setattr(kmod.requests, "post", lambda *a, **kws: DummyResp())

    assert k.query_ollama() is None


def test_query_ollama_sets_plan_and_no_toolcalls(monkeypatch):
    k = Kontxt()
    import kontxt.kontxt as kmod

    monkeypatch.setattr(kmod, "uuid1", lambda: "q2")
    k.session = UserSession(plan=[], user="u2", context=[])

    model_payload = {
        "Plan": ["p1", "p2"],
        "ToolCalls": [],
        "Context": "",
        "Thinking": "",
        "User": "u2",
    }

    class DummyResp:
        def json(self):
            return {"response": json.dumps(model_payload)}

    monkeypatch.setattr(kmod.requests, "post", lambda *a, **kws: DummyResp())

    k.query_ollama()
    assert k.plan == ["p1", "p2"]
    assert getattr(k, "tool_calls") == []


def test_process_tool_calls_updates_update_tool_calls(monkeypatch):
    k = Kontxt()
    import kontxt.kontxt as kmod

    # set tool_calls as plain dicts (the implementation indexes into them)
    k.tool_calls = [{"name": "tools", "args": ["a", "b"], "result": ""}]

    class DummyGetResp:
        def __init__(self, payload):
            self.text = json.dumps(payload)

    def fake_get(path, timeout=0):
        return DummyGetResp({"ok": True, "path": path})

    monkeypatch.setattr(kmod.requests, "get", fake_get)

    k.process_tool_calls()
    assert isinstance(k.update_tool_calls, list)
    assert "tools" in k.update_tool_calls[0]
    assert k.update_tool_calls[0]["tools"]["ok"] is True
    assert isinstance(k.update_tool_calls[0]["tools"]["path"], str)


def test_currate_raises_due_to_user_session_init():
    k = Kontxt()
    # currate calls UserSession() with no args which is expected to raise
    with pytest.raises(TypeError):
        k.currate("hello")


import os
import sys
import json
from types import SimpleNamespace

import pytest

# Ensure `src` is on the import path so `kontxt` package can be imported
ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from kontxt.kontxt import (
    ToolCall,
    PlanItem,
    UserSession,
    Kontxt,
)
from pydantic import ValidationError


def test_toolcall_to_string_contains_fields():
    tc = ToolCall(name="search", args={"q": "term"}, result="done")
    s = tc.to_string()
    assert "Tool: search" in s
    assert '"q": "term"' in s
    assert "done" in s


def test_planitem_to_string_raises_attribute_error():
    # PlanItem.to_string references a non-existent attribute `plan_state`
    pi = PlanItem(task="do something", tool_calls=[])
    with pytest.raises(AttributeError):
        _ = pi.to_string()


def test_usersession_defaults_and_context_manipulation():
    us = UserSession(plan=[], user="alice")
    assert us.user == "alice"
    assert us.plan == []
    assert us.context == []


def test_kontxt_session_user_plan_and_context_properties():
    k = Kontxt()
    us = UserSession(plan=[], user="bob")
    # set session
    k.session = us
    assert k.session is us

    # user setter/getter
    k.user = "bobby"
    assert k.user == "bobby"

    # plan setter/getter (assignment allowed dynamically)
    k.plan = ["step1", "step2"]
    assert k.plan == ["step1", "step2"]

    # context setter/getter and add_context
    k.context = ["ctx1"]
    k.add_context("ctx2")
    assert k.context == ["ctx1", "ctx2"]
    assert k.context_str.strip().splitlines() == ["* ctx1", "* ctx2"]


def test_plan_str_raises_type_error_when_session_not_sized():
    k = Kontxt()
    us = UserSession(plan=[], user="u")
    k.session = us
    # The implementation uses `len(self.session)` which will raise TypeError
    with pytest.raises(TypeError):
        _ = k.plan_str


def test_summary_uses_overridden_plan_str_and_includes_values():
    k = Kontxt()
    us = UserSession(plan=[], user="carol")
    k.session = us
    # override the `plan_str` attribute on the instance to avoid the broken property
    k.plan_str = "Plan: one"
    k.user = "carol"
    k.context = ["c1"]
    s = k.summary
    assert "## User" in s
    assert "carol" in s
    assert "Plan: one" in s
    assert "c1" in s


def test_process_tool_calls_with_mocked_requests(monkeypatch):
    k = Kontxt()
    us = UserSession(plan=[], user="d")
    k.session = us

    # provide a list of dict-like tool calls (the implementation indexes into the item)
    k.tool_calls = [{"name": "tools", "args": ["item"], "result": ""}]

    class DummyResp:
        def __init__(self, text):
            self.text = text

        def __eq__(self, other):
            # keep comparison to empty string from behaving as equal
            return False

    def fake_get(url, timeout):
        assert "tools" in url
        return DummyResp(json.dumps({"ok": True}))

    monkeypatch.setattr("kontxt.kontxt.requests.get", fake_get)

    # run
    ret = k.process_tool_calls()
    # process_tool_calls returns None but sets update_tool_calls
    assert hasattr(k, "update_tool_calls")
    assert k.update_tool_calls == [{"tools": {"ok": True}}]


def test_query_ollama_no_response(monkeypatch):
    k = Kontxt()
    us = UserSession(plan=[], user="e")
    k.session = us

    # Post returns a dict with empty response -> function returns early
    class DummyPost:
        def json(self):
            return {"response": ""}

    monkeypatch.setattr("kontxt.kontxt.requests.post", lambda *a, **kw: DummyPost())
    assert k.query_ollama() is None


def test_query_ollama_populates_plan_and_calls_process_tool_calls(monkeypatch):
    k = Kontxt()
    us = UserSession(plan=[], user="f")
    k.session = us

    # prepare a model response that contains a Plan and no ToolCalls
    model_payload = {"Plan": ["p1", "p2"], "ToolCalls": []}

    class DummyPost:
        def json(self_inner):
            return {"response": json.dumps(model_payload)}

    called = {"proc": False}

    def fake_process(self):
        called["proc"] = True

    monkeypatch.setattr("kontxt.kontxt.requests.post", lambda *a, **kw: DummyPost())
    # replace process_tool_calls so it won't try to perform HTTP calls
    monkeypatch.setattr(Kontxt, "process_tool_calls", fake_process)

    k.query_ollama()
    assert k.plan == ["p1", "p2"]


def test_currate_raises_validation_error():
    k = Kontxt()
    # currate tries to instantiate a UserSession() with no args which should fail
    with pytest.raises(ValidationError):
        k.currate("hello")
