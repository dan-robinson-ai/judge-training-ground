"""DSPy optimizer factory implementation."""

from app.services.optimizer.base import OptimizationConfig, OptimizerAdapter
from app.services.optimizer.dspy.adapters import (
    BootstrapFewShotAdapter,
    COPROAdapter,
    MIPROv2Adapter,
)


class DSPyOptimizerFactory:
    """Factory for creating DSPy optimizer adapters."""

    OPTIMIZER_MAP = {
        "bootstrap_fewshot": BootstrapFewShotAdapter,
        "miprov2": MIPROv2Adapter,
        "copro": COPROAdapter,
    }

    def get_optimizer_types(self) -> list[str]:
        """Return list of supported optimizer type names."""
        return list(self.OPTIMIZER_MAP.keys())

    def create_adapter(
        self,
        optimizer_type: str,
        config: OptimizationConfig,
    ) -> OptimizerAdapter:
        """Create an optimizer adapter for the given type."""
        if optimizer_type not in self.OPTIMIZER_MAP:
            raise ValueError(
                f"Unknown DSPy optimizer: {optimizer_type}. "
                f"Available: {list(self.OPTIMIZER_MAP.keys())}"
            )

        adapter_class = self.OPTIMIZER_MAP[optimizer_type]
        return adapter_class(config)
