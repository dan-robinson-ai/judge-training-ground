"""Abstract base classes for optimizer framework."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas import TestCase


@dataclass
class OptimizationConfig:
    """Configuration for optimization run."""

    model: str
    n_threads: int = 8
    seed: int = 42
    verbose: int = 0


class OptimizerAdapter(ABC):
    """Abstract base class for optimizer adapters.

    Each adapter wraps a specific optimizer from DSPy or Opik,
    converting inputs/outputs to the common format.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the optimizer name."""
        pass

    @property
    @abstractmethod
    def framework(self) -> str:
        """Return the framework name ('dspy' or 'opik')."""
        pass

    @abstractmethod
    async def optimize(
        self,
        current_prompt: str,
        train_cases: list[TestCase],
        config: OptimizationConfig,
    ) -> tuple[str, str]:
        """Run optimization and return (optimized_prompt, modification_notes)."""
        pass
