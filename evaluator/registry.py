"""Registry for evaluation suites and agent implementations."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any, Callable, Dict, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from evaluator.orchestrator import EvalSuite

T = TypeVar("T", bound=Callable)

_SUITES: Dict[str, Any] = {}
_AGENT_RUNNERS: Dict[str, Callable[..., list[str]]] = {}


def register_suite(suite: "EvalSuite") -> "EvalSuite":
    """Register an evaluation suite."""
    _SUITES[suite.name] = suite
    return suite


def register_agent(name: str) -> Callable[[T], T]:
    """Decorator to register an agent runner.
    
    The runner should be a function that accepts (task, model, suite_name) 
    and returns a list of command-line arguments to execute.
    """
    def decorator(func: T) -> T:
        _AGENT_RUNNERS[name] = func
        return func
    return decorator


def get_suite(name: str) -> EvalSuite | None:
    """Retrieve a registered suite by name."""
    return _SUITES.get(name)


def get_agent_runner(name: str) -> Callable[..., list[str]] | None:
    """Retrieve a registered agent runner by name."""
    return _AGENT_RUNNERS.get(name)


def list_suites() -> list[str]:
    """List all registered suite names."""
    return list(_SUITES.keys())


def list_agents() -> list[str]:
    """List all registered agent names."""
    return list(_AGENT_RUNNERS.keys())


def discover_plugins(package_name: str):
    """Dynamically import all modules in a package to trigger registration."""
    package = importlib.import_module(package_name)
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        importlib.import_module(name)
