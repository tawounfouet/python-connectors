"""
Exemple d'utilisation des connecteurs de réseaux sociaux.

Ce script démontre comment utiliser les différents connecteurs pour :
- Se connecter aux réseaux sociaux
- Publier du contenu
- Récupérer le flux
- Obtenir les informations de profil
"""

import os
from datetime import datetime
from connectors import create_connector, list_available_connectors

def main():
    """Fonction principale d'exemple."""
    
    print("=== Connecteurs de Réseaux Sociaux Disponibles ===")
    connectors = list_available_connectors()
    social_connectors = {k: v for k, v in connectors.items() 
                        if k in ['twitter', 'facebook', 'instagram', 'linkedin', 'youtube', 'tiktok']}
    
    for name, class_name in social_connectors.items():
        print(f"- {name}: {class_name}")
    
    print("\n=== Exemple avec Twitter ===")
    twitter_example()
    
    print("\n=== Exemple avec LinkedIn ===")
    linkedin_example()
    
    print("\n=== Exemple avec Facebook ===")
    facebook_example()


def twitter_example():
    """Exemple d'utilisation du connecteur Twitter."""
    
    # Configuration Twitter
    config = {
        'bearer_token': os.getenv('TWITTER_BEARER_TOKEN', 'your_bearer_token'),
        'api_key': os.getenv('TWITTER_API_KEY', 'your_api_key'),
        'api_secret': os.getenv('TWITTER_API_SECRET', 'your_api_secret'),
        'access_token': os.getenv('TWITTER_ACCESS_TOKEN', 'your_access_token'),
        'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET', 'your_access_token_secret')
    }
    
    try:
        # Création du connecteur
        twitter = create_connector("twitter", config, "my_twitter")
        
        # Connexion
        if twitter.connect():
            print("✅ Connexion à Twitter réussie")
            
            # Test de connexion
            if twitter.test_connection():
                print("✅ Test de connexion réussi")
                
                # Récupération des informations du profil
                profile = twitter.get_profile_info()
                print(f"📱 Profil: @{profile.get('username', 'unknown')} "
                      f"({profile.get('followers_count', 0)} abonnés)")
                
                # Publication d'un tweet (exemple - ne pas exécuter en production)
                # message = f"Tweet automatique depuis Python - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                # tweet = twitter.post_message(message)
                # print(f"📤 Tweet publié: {tweet.get('url', 'N/A')}")
                
                # Récupération du flux
                feed = twitter.get_feed(limit=5)
                print(f"📰 Récupéré {len(feed)} tweets du flux")
                
                for i, tweet in enumerate(feed[:3], 1):
                    print(f"  {i}. {tweet.get('text', '')[:80]}...")
                
                # Informations sur les limites de taux
                rate_info = twitter.get_rate_limit_info()
                if rate_info:
                    print(f"⚡ Rate limit: {rate_info.get('remaining', 'N/A')}/{rate_info.get('limit', 'N/A')} restantes")
            
        else:
            print("❌ Échec de la connexion à Twitter")
    
    except Exception as e:
        print(f"❌ Erreur Twitter: {e}")
    
    finally:
        if 'twitter' in locals():
            twitter.disconnect()
            print("🔌 Déconnexion de Twitter")


def linkedin_example():
    """Exemple d'utilisation du connecteur LinkedIn."""
    
    # Configuration LinkedIn
    config = {
        'access_token': os.getenv('LINKEDIN_ACCESS_TOKEN', 'your_access_token'),
        'client_id': os.getenv('LINKEDIN_CLIENT_ID', 'your_client_id'),
        'client_secret': os.getenv('LINKEDIN_CLIENT_SECRET', 'your_client_secret')
    }
    
    try:
        # Création du connecteur
        linkedin = create_connector("linkedin", config, "my_linkedin")
        
        # Connexion
        if linkedin.connect():
            print("✅ Connexion à LinkedIn réussie")
            
            # Récupération des informations du profil
            profile = linkedin.get_profile_info()
            print(f"👔 Profil: {profile.get('name', 'unknown')} - {profile.get('headline', '')}")
            
            # Publication d'un post (exemple - ne pas exécuter en production)
            # message = f"Post automatique depuis Python - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            # options = {'visibility': 'PUBLIC'}
            # post = linkedin.post_message(message, options=options)
            # print(f"📤 Post LinkedIn publié: {post.get('url', 'N/A')}")
            
            # Récupération du flux
            feed = linkedin.get_feed(limit=5)
            print(f"📰 Récupéré {len(feed)} posts du flux")
            
            # Récupération des connexions
            connections = linkedin.get_connections(limit=10)
            print(f"🤝 {len(connections)} connexions récupérées")
        
        else:
            print("❌ Échec de la connexion à LinkedIn")
    
    except Exception as e:
        print(f"❌ Erreur LinkedIn: {e}")
    
    finally:
        if 'linkedin' in locals():
            linkedin.disconnect()
            print("🔌 Déconnexion de LinkedIn")


def facebook_example():
    """Exemple d'utilisation du connecteur Facebook."""
    
    # Configuration Facebook
    config = {
        'access_token': os.getenv('FACEBOOK_ACCESS_TOKEN', 'your_access_token'),
        'page_id': os.getenv('FACEBOOK_PAGE_ID')  # Optionnel pour les pages
    }
    
    try:
        # Création du connecteur
        facebook = create_connector("facebook", config, "my_facebook")
        
        # Connexion
        if facebook.connect():
            print("✅ Connexion à Facebook réussie")
            
            # Récupération des informations du profil
            profile = facebook.get_profile_info()
            print(f"👤 Profil Facebook: {profile.get('name', 'unknown')}")
            
            # Publication d'un post (exemple - ne pas exécuter en production)
            # message = f"Post automatique depuis Python - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            # post = facebook.post_message(message)
            # print(f"📤 Post Facebook publié: {post.get('url', 'N/A')}")
            
            # Récupération du flux
            feed = facebook.get_feed(limit=5)
            print(f"📰 Récupéré {len(feed)} posts du flux")
        
        else:
            print("❌ Échec de la connexion à Facebook")
    
    except Exception as e:
        print(f"❌ Erreur Facebook: {e}")
    
    finally:
        if 'facebook' in locals():
            facebook.disconnect()
            print("🔌 Déconnexion de Facebook")


def show_social_media_best_practices():
    """Affiche les bonnes pratiques pour les réseaux sociaux."""
    
    print("\n=== 🎯 Bonnes Pratiques pour les Réseaux Sociaux ===")
    
    practices = [
        "🔑 Stockez vos tokens d'API de manière sécurisée (variables d'environnement)",
        "⏱️ Respectez les limites de taux de chaque plateforme",
        "🔄 Implémentez une logique de retry avec backoff exponentiel",
        "📝 Validez le contenu avant publication (longueur, format, etc.)",
        "🛡️ Gérez les erreurs d'API de manière gracieuse",
        "📊 Surveillez les métriques d'utilisation de l'API",
        "🔐 Utilisez OAuth 2.0 quand c'est possible",
        "📱 Testez sur un compte de développement avant la production",
        "💾 Gardez une trace des publications pour éviter les doublons",
        "🚫 Ne jamais publier de contenu sensible ou non vérifié"
    ]
    
    for practice in practices:
        print(f"  {practice}")
    
    print("\n=== 📚 Documentation API Officielle ===")
    docs = {
        "Twitter": "https://developer.twitter.com/en/docs/twitter-api",
        "LinkedIn": "https://docs.microsoft.com/en-us/linkedin/",
        "Facebook": "https://developers.facebook.com/docs/graph-api/",
        "Instagram": "https://developers.facebook.com/docs/instagram-api/",
        "YouTube": "https://developers.google.com/youtube/v3",
        "TikTok": "https://developers.tiktok.com/"
    }
    
    for platform, url in docs.items():
        print(f"  {platform}: {url}")


if __name__ == "__main__":
    print("🚀 Démonstration des Connecteurs de Réseaux Sociaux")
    print("=" * 60)
    
    main()
    show_social_media_best_practices()
    
    print("\n✨ Fin de la démonstration")
    print("Note: Pour utiliser les connecteurs en production, configurez vos tokens d'API réels.")
