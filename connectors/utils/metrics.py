"""
Collecteur de métriques pour les connecteurs.
"""

import time
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class OperationMetric:
    """Métrique pour une opération."""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Durée de l'opération en secondes."""
        if self.end_time is not None:
            return self.end_time - self.start_time
        return None


@dataclass
class ConnectorMetrics:
    """Métriques globales d'un connecteur."""
    connector_name: str
    operations: List[OperationMetric] = field(default_factory=list)
    connection_count: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_duration: float = 0.0
    
    def add_operation(self, metric: OperationMetric):
        """Ajoute une métrique d'opération."""
        self.operations.append(metric)
        if metric.success:
            self.successful_operations += 1
        else:
            self.failed_operations += 1
        
        if metric.duration is not None:
            self.total_duration += metric.duration
    
    @property
    def success_rate(self) -> float:
        """Taux de succès des opérations."""
        total = self.successful_operations + self.failed_operations
        if total == 0:
            return 0.0
        return self.successful_operations / total
    
    @property
    def average_duration(self) -> float:
        """Durée moyenne des opérations."""
        if not self.operations:
            return 0.0
        completed_ops = [op for op in self.operations if op.duration is not None]
        if not completed_ops:
            return 0.0
        return sum(op.duration for op in completed_ops) / len(completed_ops)


class MetricsCollector:
    """Collecteur de métriques thread-safe."""
    
    def __init__(self, connector_name: str):
        self.connector_name = connector_name
        self.metrics = ConnectorMetrics(connector_name)
        self._lock = threading.Lock()
    
    def start_operation(self, operation_name: str) -> OperationMetric:
        """Démarre le suivi d'une opération."""
        metric = OperationMetric(
            operation_name=operation_name,
            start_time=time.time()
        )
        logger.debug(f"Started operation: {operation_name}")
        return metric
    
    def end_operation(self, metric: OperationMetric, success: bool = True, 
                     error_message: Optional[str] = None):
        """Termine le suivi d'une opération."""
        metric.end_time = time.time()
        metric.success = success
        metric.error_message = error_message
        
        with self._lock:
            self.metrics.add_operation(metric)
        
        status = "SUCCESS" if success else "FAILED"
        logger.debug(f"Ended operation: {metric.operation_name} - {status} - Duration: {metric.duration:.3f}s")
    
    def increment_connection_count(self):
        """Incrémente le compteur de connexions."""
        with self._lock:
            self.metrics.connection_count += 1
    
    def get_metrics(self) -> ConnectorMetrics:
        """Retourne une copie des métriques actuelles."""
        with self._lock:
            return ConnectorMetrics(
                connector_name=self.metrics.connector_name,
                operations=self.metrics.operations.copy(),
                connection_count=self.metrics.connection_count,
                successful_operations=self.metrics.successful_operations,
                failed_operations=self.metrics.failed_operations,
                total_duration=self.metrics.total_duration
            )
    
    def reset_metrics(self):
        """Remet à zéro toutes les métriques."""
        with self._lock:
            self.metrics = ConnectorMetrics(self.connector_name)
        logger.info(f"Metrics reset for connector: {self.connector_name}")
    
    def log_summary(self):
        """Log un résumé des métriques."""
        metrics = self.get_metrics()
        logger.info(f"""
Metrics Summary for {self.connector_name}:
- Total Operations: {len(metrics.operations)}
- Success Rate: {metrics.success_rate:.2%}
- Average Duration: {metrics.average_duration:.3f}s
- Total Connections: {metrics.connection_count}
        """.strip())
