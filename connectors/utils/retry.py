"""
Utilitaires pour les tentatives de retry.
"""

import time
import random
import logging
from functools import wraps
from typing import Callable, Type, Union, Tuple

from ..exceptions import RetryExhaustedError

logger = logging.getLogger(__name__)


def retry_on_exception(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    jitter: bool = True
):
    """
    Décorateur pour retry automatique sur exceptions.
    
    Args:
        max_attempts: Nombre maximum de tentatives
        backoff_factor: Facteur d'augmentation du délai entre tentatives
        initial_delay: Délai initial en secondes
        max_delay: Délai maximum en secondes
        exceptions: Exception(s) sur lesquelles faire un retry
        jitter: Ajouter un délai aléatoire pour éviter les pics de charge
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"Retry exhausted after {max_attempts} attempts for {func.__name__}: {e}")
                        raise RetryExhaustedError(f"Failed after {max_attempts} attempts: {e}") from e
                    
                    # Calcul du délai avec backoff exponentiel
                    delay = min(initial_delay * (backoff_factor ** attempt), max_delay)
                    
                    # Ajout de jitter pour éviter les pics de charge
                    if jitter:
                        delay += random.uniform(0, delay * 0.1)
                    
                    logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                    time.sleep(delay)
            
            # Cette ligne ne devrait jamais être atteinte
            raise last_exception
        
        return wrapper
    return decorator


class RetryManager:
    """Gestionnaire de retry pour les connecteurs."""
    
    def __init__(self, max_attempts: int = 3, backoff_factor: float = 2.0, 
                 initial_delay: float = 1.0, max_delay: float = 60.0):
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay
        self.max_delay = max_delay
    
    def execute_with_retry(self, func: Callable, *args, **kwargs):
        """Exécute une fonction avec retry."""
        decorated_func = retry_on_exception(
            max_attempts=self.max_attempts,
            backoff_factor=self.backoff_factor,
            initial_delay=self.initial_delay,
            max_delay=self.max_delay
        )(func)
        
        return decorated_func(*args, **kwargs)
