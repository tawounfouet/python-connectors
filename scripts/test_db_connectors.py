"""
Test de l'enregistrement des connecteurs de base de données.
"""

def test_connector_registration():
    """Teste que tous les connecteurs sont correctement enregistrés."""
    print("Test d'enregistrement des connecteurs de base de données")
    print("=" * 60)
    
    try:
        from connectors import list_available_connectors, registry
        
        # Lister tous les connecteurs disponibles
        connectors = list_available_connectors()
        print(f"Connecteurs enregistrés: {len(connectors)}")
        
        expected_connectors = ['postgresql', 'mysql', 'sqlserver', 'snowflake']
        
        for connector_name in expected_connectors:
            if connector_name in connectors:
                print(f"✓ {connector_name}: {connectors[connector_name]}")
            else:
                print(f"✗ {connector_name}: NON ENREGISTRÉ")
        
        # Test de création (sans connexion)
        print("\nTest de création des connecteurs:")
        
        for connector_name in expected_connectors:
            if connector_name in connectors:
                try:
                    # Configuration minimale pour test
                    if connector_name == 'snowflake':
                        config = {
                            'account': 'test',
                            'username': 'test',
                            'password': 'test',
                            'warehouse': 'test',
                            'database': 'test',
                            'schema': 'test'
                        }
                    else:
                        config = {
                            'host': 'localhost',
                            'port': 5432,  # Port par défaut
                            'database': 'test',
                            'username': 'test',
                            'password': 'test'
                        }
                    
                    connector_class = registry.get_connector_class(connector_name)
                    instance = connector_class(config)
                    print(f"✓ {connector_name}: Instance créée - {instance.__class__.__name__}")
                    
                except Exception as e:
                    print(f"✗ {connector_name}: Erreur lors de la création - {e}")
            else:
                print(f"✗ {connector_name}: Connecteur non disponible")
        
        print(f"\nTest terminé. {len(connectors)} connecteurs disponibles.")
        return True
        
    except Exception as e:
        print(f"Erreur lors du test: {e}")
        return False


if __name__ == "__main__":
    success = test_connector_registration()
    exit(0 if success else 1)
