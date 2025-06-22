#!/usr/bin/env python3
"""
Script de test d'intégration pour les connecteurs de réseaux sociaux.

Ce script vérifie que tous les connecteurs peuvent être importés et instanciés
correctement, sans nécessiter de vrais tokens d'API.
"""

import sys
import os
import traceback
from typing import Dict, Any, List

# Ajouter le chemin du module au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test l'importation de tous les modules de connecteurs sociaux."""
    print("🔍 Test des imports...")
    
    try:
        # Test d'import du module principal
        from connectors import create_connector, list_available_connectors
        print("  ✅ Module principal importé")
        
        # Test d'import des connecteurs
        from connectors.social_media import (
            SocialMediaConnector,
            TwitterConnector,
            FacebookConnector,
            InstagramConnector,
            LinkedInConnector,
            YouTubeConnector,
            TikTokConnector
        )
        print("  ✅ Connecteurs de réseaux sociaux importés")
        
        # Test d'import des configurations
        from connectors.config import (
            SocialMediaConfig,
            TwitterConfig,
            LinkedInConfig,
            FacebookConfig,
            InstagramConfig,
            YouTubeConfig,
            TikTokConfig
        )
        print("  ✅ Configurations importées")
        
        # Test d'import des exceptions
        from connectors.exceptions.connector_exceptions import (
            SocialMediaConnectionError,
            SocialMediaAuthenticationError,
            SocialMediaAPIError
        )
        print("  ✅ Exceptions importées")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Erreur d'import: {e}")
        traceback.print_exc()
        return False


def test_connector_registration():
    """Test l'enregistrement des connecteurs dans le registre."""
    print("\n📝 Test de l'enregistrement des connecteurs...")
    
    try:
        from connectors import list_available_connectors
        
        connectors = list_available_connectors()
        social_connectors = [
            'twitter', 'facebook', 'instagram', 
            'linkedin', 'youtube', 'tiktok'
        ]
        
        registered_social = [name for name in social_connectors if name in connectors]
        
        print(f"  📊 Connecteurs sociaux enregistrés: {len(registered_social)}/{len(social_connectors)}")
        
        for connector in social_connectors:
            status = "✅" if connector in connectors else "❌"
            print(f"    {status} {connector}")
        
        return len(registered_social) == len(social_connectors)
        
    except Exception as e:
        print(f"  ❌ Erreur lors du test d'enregistrement: {e}")
        traceback.print_exc()
        return False


def test_connector_instantiation():
    """Test l'instanciation des connecteurs avec des configurations de test."""
    print("\n🏗️ Test d'instanciation des connecteurs...")
    
    test_configs = {
        'twitter': {
            'bearer_token': 'test_bearer_token_1234567890'
        },
        'linkedin': {
            'access_token': 'test_access_token_1234567890'
        },
        'facebook': {
            'access_token': 'test_access_token_1234567890'
        },
        'instagram': {
            'access_token': 'test_access_token_1234567890'
        },
        'youtube': {
            'api_key': 'test_api_key_1234567890'
        },
        'tiktok': {
            'access_token': 'test_access_token_1234567890'
        }
    }
    
    success_count = 0
    total_count = len(test_configs)
    
    try:
        from connectors import create_connector
        
        for platform, config in test_configs.items():
            try:
                connector = create_connector(platform, config, f"test_{platform}")
                print(f"  ✅ {platform}: Instanciation réussie")
                
                # Test des propriétés de base
                assert hasattr(connector, 'platform_name')
                assert hasattr(connector, 'authenticate')
                assert hasattr(connector, 'post_message')
                assert hasattr(connector, 'get_feed')
                assert hasattr(connector, 'get_profile_info')
                assert hasattr(connector, 'delete_post')
                
                print(f"     🔧 Interface complète vérifiée")
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ {platform}: Erreur d'instanciation - {e}")
        
        print(f"\n  📊 Résultat: {success_count}/{total_count} connecteurs instanciés avec succès")
        return success_count == total_count
        
    except Exception as e:
        print(f"  ❌ Erreur générale lors des tests d'instanciation: {e}")
        traceback.print_exc()
        return False


def test_configuration_validation():
    """Test la validation des configurations."""
    print("\n🔧 Test de validation des configurations...")
    
    try:
        from connectors.config import (
            TwitterConfig, LinkedInConfig, FacebookConfig,
            InstagramConfig, YouTubeConfig, TikTokConfig
        )
        
        test_cases = [
            # Configurations valides
            ('TwitterConfig', TwitterConfig, {'bearer_token': 'valid_token_1234567890'}, True),
            ('LinkedInConfig', LinkedInConfig, {'access_token': 'valid_token_1234567890'}, True),
            ('FacebookConfig', FacebookConfig, {'access_token': 'valid_token_1234567890'}, True),
            ('InstagramConfig', InstagramConfig, {'access_token': 'valid_token_1234567890'}, True),
            ('YouTubeConfig', YouTubeConfig, {'api_key': 'valid_key_1234567890'}, True),
            ('TikTokConfig', TikTokConfig, {'access_token': 'valid_token_1234567890'}, True),
            
            # Configurations invalides
            ('TwitterConfig', TwitterConfig, {'bearer_token': 'short'}, False),
            ('LinkedInConfig', LinkedInConfig, {'access_token': 'short'}, False),
            ('FacebookConfig', FacebookConfig, {'access_token': 'short'}, False),
            ('InstagramConfig', InstagramConfig, {'access_token': 'short'}, False),
            ('YouTubeConfig', YouTubeConfig, {'api_key': 'short'}, False),
            ('TikTokConfig', TikTokConfig, {'access_token': 'short'}, False),
        ]
        
        success_count = 0
        
        for config_name, config_class, data, should_succeed in test_cases:
            try:
                config = config_class(**data)
                if should_succeed:
                    print(f"  ✅ {config_name}: Validation réussie (attendue)")
                    success_count += 1
                else:
                    print(f"  ❌ {config_name}: Validation réussie mais échec attendu")
                    
            except Exception as e:
                if not should_succeed:
                    print(f"  ✅ {config_name}: Validation échouée (attendue)")
                    success_count += 1
                else:
                    print(f"  ❌ {config_name}: Validation échouée - {e}")
        
        print(f"\n  📊 Tests de validation: {success_count}/{len(test_cases)} réussis")
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"  ❌ Erreur lors des tests de validation: {e}")
        traceback.print_exc()
        return False


def test_error_handling():
    """Test la gestion des erreurs."""
    print("\n🚨 Test de gestion des erreurs...")
    
    try:
        from connectors.exceptions.connector_exceptions import (
            SocialMediaConnectionError,
            SocialMediaAuthenticationError,
            SocialMediaAPIError
        )
        
        # Test que les exceptions peuvent être levées et attrapées
        test_cases = [
            SocialMediaConnectionError("Test connection error"),
            SocialMediaAuthenticationError("Test auth error"),
            SocialMediaAPIError("Test API error")
        ]
        
        for exception in test_cases:
            try:
                raise exception
            except type(exception) as e:
                print(f"  ✅ {type(exception).__name__}: Exception gérée correctement")
            except Exception as e:
                print(f"  ❌ {type(exception).__name__}: Exception non gérée - {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur lors des tests de gestion d'erreurs: {e}")
        traceback.print_exc()
        return False


def run_all_tests():
    """Exécute tous les tests."""
    print("🚀 Démarrage des tests d'intégration des connecteurs de réseaux sociaux")
    print("=" * 80)
    
    tests = [
        ("Imports", test_imports),
        ("Enregistrement des connecteurs", test_connector_registration),
        ("Instanciation des connecteurs", test_connector_instantiation),
        ("Validation des configurations", test_configuration_validation),
        ("Gestion des erreurs", test_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Test: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: RÉUSSI")
            else:
                print(f"❌ {test_name}: ÉCHEC")
                
        except Exception as e:
            print(f"💥 {test_name}: ERREUR CRITIQUE - {e}")
            traceback.print_exc()
            results.append((test_name, False))
    
    # Résumé des résultats
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"{status:12} | {test_name}")
    
    print("-" * 80)
    print(f"TOTAL: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("\nLes connecteurs de réseaux sociaux sont prêts à être utilisés.")
        return 0
    else:
        print("⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        print("\nVeuillez corriger les erreurs avant d'utiliser les connecteurs.")
        return 1


def main():
    """Fonction principale."""
    try:
        return run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrompus par l'utilisateur")
        return 130
    except Exception as e:
        print(f"\n\n💥 Erreur critique dans les tests: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
