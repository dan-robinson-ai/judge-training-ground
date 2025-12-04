"""Opik optimizer factory implementation."""

from app.services.optimizer.base import OptimizationConfig, OptimizerAdapter
from app.services.optimizer.opik.adapters import (
    EvolutionaryOptimizerAdapter,
    FewShotBayesianAdapter,
    GepaAdapter,
    HierarchicalReflectiveAdapter,
    MetaPromptAdapter,
    ParameterAdapter,
)


class OpikOptimizerFactory:
    """Factory for creating Opik optimizer adapters."""

    OPTIMIZER_MAP = {
        "evolutionary": EvolutionaryOptimizerAdapter,
        "fewshot_bayesian": FewShotBayesianAdapter,
        "metaprompt": MetaPromptAdapter,
        "hierarchical_reflective": HierarchicalReflectiveAdapter,
        "gepa": GepaAdapter,
        "parameter": ParameterAdapter,
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
                f"Unknown Opik optimizer: {optimizer_type}. "
                f"Available: {list(self.OPTIMIZER_MAP.keys())}"
            )

        adapter_class = self.OPTIMIZER_MAP[optimizer_type]
        return adapter_class(config)
